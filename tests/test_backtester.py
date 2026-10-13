import pandas as pd
import pytest

from backtester import run_backtest


def test_bear_exit_and_48_hour_cooldown():
    index = pd.date_range("2025-01-01", periods=56, freq="h", tz="UTC")
    frame = pd.DataFrame(
        {
            "Open": [100, 100, 102, 103] + [100] * 52,
            "Close": [100] * 56,
            "Regime": ["Bull Run", "Bull Run", "Bear / Crash"] + ["Bull Run"] * 53,
            "Confirmation_Count": [8] * 56,
        },
        index=index,
    )
    result = run_backtest(frame)
    assert len(result.trades) == 1
    assert result.trades.iloc[0]["Entry Time"] == index[1]
    assert result.trades.iloc[0]["Exit Time"] == index[3]
    assert result.trades.iloc[0]["PnL"] == pytest.approx(750.0)
    # Earliest re-entry is exactly 48 hours after the exit.
    assert result.frame.loc[index[50], "Position"] == 0
    assert result.frame.loc[index[51], "Position"] == 1


def test_requires_seven_confirmations_and_bull_regime():
    index = pd.date_range("2025-01-01", periods=4, freq="h", tz="UTC")
    frame = pd.DataFrame(
        {
            "Open": [100, 100, 100, 100],
            "Close": [100, 100, 100, 100],
            "Regime": ["Bull Run", "Neutral 2", "Bull Run", "Neutral 1"],
            "Confirmation_Count": [6, 8, 7, 0],
        },
        index=index,
    )
    result = run_backtest(frame)
    assert result.frame["Position"].tolist() == [0, 0, 0, 1]

