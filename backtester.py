"""Long-only regime strategy backtester with 2.5x simulated leverage."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from config import CONFIG


@dataclass
class BacktestResult:
    frame: pd.DataFrame
    trades: pd.DataFrame
    metrics: dict[str, float]
    current_position: str
    cooldown_until: pd.Timestamp | None


TRADE_COLUMNS = [
    "Entry Time",
    "Exit Time",
    "Entry Price",
    "Exit Price",
    "Entry Confirmations",
    "Exit Regime",
    "Exit Reason",
    "Unlevered Return",
    "Leveraged Return",
    "PnL",
    "Capital After",
    "Holding Hours",
]


def run_backtest(
    data: pd.DataFrame,
    initial_capital: float = CONFIG.initial_capital,
    leverage: float = CONFIG.leverage,
    cooldown_hours: int = CONFIG.cooldown_hours,
    required_confirmations: int = CONFIG.required_confirmations,
) -> BacktestResult:
    required = {"Open", "Close", "Regime", "Confirmation_Count"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing backtest columns: {sorted(missing)}")
    if data.empty:
        raise ValueError("Cannot backtest an empty data set")

    frame = data.copy().sort_index()
    if frame.index.tz is None:
        frame.index = frame.index.tz_localize("UTC")

    capital = float(initial_capital)
    in_position = False
    entry_price = 0.0
    entry_time: pd.Timestamp | None = None
    entry_capital = 0.0
    entry_confirmations = 0
    cooldown_until: pd.Timestamp | None = None
    trades: list[dict[str, object]] = []
    equities: list[float] = []
    positions: list[int] = []
    entry_signals: list[bool] = []

    def close_position(timestamp: pd.Timestamp, price: float, regime: str, reason: str) -> None:
        nonlocal capital, in_position, cooldown_until
        unlevered_return = price / entry_price - 1
        leveraged_return = leverage * unlevered_return
        pnl = entry_capital * leveraged_return
        capital = entry_capital + pnl
        trades.append(
            {
                "Entry Time": entry_time,
                "Exit Time": timestamp,
                "Entry Price": entry_price,
                "Exit Price": price,
                "Entry Confirmations": entry_confirmations,
                "Exit Regime": regime,
                "Exit Reason": reason,
                "Unlevered Return": unlevered_return,
                "Leveraged Return": leveraged_return,
                "PnL": pnl,
                "Capital After": capital,
                "Holding Hours": (timestamp - entry_time).total_seconds() / 3600,
            }
        )
        in_position = False
        cooldown_until = timestamp + pd.Timedelta(hours=cooldown_hours)

    for offset, (timestamp, row) in enumerate(frame.iterrows()):
        price = float(row["Close"])
        current_regime = str(row["Regime"])
        current_confirmations = int(row["Confirmation_Count"])
        entry_signals.append(
            current_regime == "Bull Run" and current_confirmations >= required_confirmations
        )

        # A signal is known only after its candle closes, so it executes at
        # the following candle's open. This removes same-bar look-ahead.
        if offset > 0:
            signal = frame.iloc[offset - 1]
            signal_regime = str(signal["Regime"])
            signal_confirmations = int(signal["Confirmation_Count"])
            signal_eligible = signal_regime == "Bull Run" and signal_confirmations >= required_confirmations
            execution_price = float(row["Open"])

            if in_position and signal_regime == "Bear / Crash":
                close_position(timestamp, execution_price, signal_regime, "Bear / Crash regime")

            if (
                not in_position
                and capital > 0
                and signal_eligible
                and (cooldown_until is None or timestamp >= cooldown_until)
            ):
                in_position = True
                entry_price = execution_price
                entry_time = timestamp
                entry_capital = capital
                entry_confirmations = signal_confirmations

        equity = capital
        if in_position:
            equity = entry_capital * (1 + leverage * (price / entry_price - 1))
        equities.append(equity)
        positions.append(int(in_position))

    if in_position:
        timestamp = frame.index[-1]
        price = float(frame["Close"].iloc[-1])
        # Keep the current position open for the live signal. Its unrealized
        # value is already represented in the final equity curve.
        final_equity = entry_capital * (1 + leverage * (price / entry_price - 1))
    else:
        final_equity = capital

    frame["Entry_Signal"] = entry_signals
    frame["Position"] = positions
    frame["Equity"] = equities
    frame["Equity_Peak"] = frame["Equity"].cummax()
    frame["Drawdown"] = frame["Equity"] / frame["Equity_Peak"] - 1

    buy_hold_return = float(frame["Close"].iloc[-1] / frame["Close"].iloc[0] - 1)
    total_return = float(final_equity / initial_capital - 1)
    trade_frame = pd.DataFrame(trades, columns=TRADE_COLUMNS)
    win_rate = float((trade_frame["PnL"] > 0).mean()) if not trade_frame.empty else 0.0
    metrics = {
        "Total Return": total_return,
        "Buy & Hold Return": buy_hold_return,
        "Alpha vs Buy & Hold": total_return - buy_hold_return,
        "Win Rate": win_rate,
        "Max Drawdown": float(frame["Drawdown"].min()),
        "Final Equity": float(final_equity),
        "Closed Trades": float(len(trade_frame)),
    }
    return BacktestResult(
        frame=frame,
        trades=trade_frame,
        metrics=metrics,
        current_position="Long" if in_position else "Cash",
        cooldown_until=cooldown_until,
    )

