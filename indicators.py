"""Technical indicators and the eight strategy confirmations."""

from __future__ import annotations

import numpy as np
import pandas as pd


CONFIRMATION_COLUMNS = [
    "RSI < 90",
    "Momentum > 1%",
    "Volatility < 6%",
    "Volume > SMA20",
    "ADX > 25",
    "Price > EMA50",
    "Price > EMA200",
    "MACD > Signal",
]


def _wilder_average(values: pd.Series, period: int) -> pd.Series:
    return values.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def calculate_indicators(data: pd.DataFrame) -> pd.DataFrame:
    df = data.copy()
    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    df["Returns"] = close.pct_change()
    df["Range"] = (high - low) / close
    # Volatility of hourly log-volume changes over the last 24 hours. log1p
    # keeps legitimate zero-volume Yahoo candles finite instead of discarding
    # most of the HMM training set.
    volume_change = np.log1p(df["Volume"].clip(lower=0)).diff()
    df["Volume_Volatility"] = volume_change.rolling(24, min_periods=12).std()

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = _wilder_average(gain, 14)
    avg_loss = _wilder_average(loss, 14)
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["RSI"] = (100 - (100 / (1 + rs))).fillna(50.0)

    df["Momentum"] = close.pct_change(24)
    # 24-hour realized volatility, expressed as a decimal (0.06 == 6%).
    df["Volatility"] = np.sqrt(df["Returns"].pow(2).rolling(24).sum())
    df["Volume_SMA20"] = df["Volume"].rolling(20).mean()
    df["EMA50"] = close.ewm(span=50, adjust=False).mean()
    df["EMA200"] = close.ewm(span=200, adjust=False).mean()
    df["MACD"] = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=df.index)
    true_range = pd.concat(
        [(high - low), (high - close.shift()).abs(), (low - close.shift()).abs()],
        axis=1,
    ).max(axis=1)
    atr = _wilder_average(true_range, 14)
    plus_di = 100 * _wilder_average(plus_dm, 14) / atr.replace(0, np.nan)
    minus_di = 100 * _wilder_average(minus_dm, 14) / atr.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    df["ADX"] = _wilder_average(dx, 14)

    confirmations = pd.DataFrame(index=df.index)
    confirmations["RSI < 90"] = df["RSI"] < 90
    confirmations["Momentum > 1%"] = df["Momentum"] > 0.01
    confirmations["Volatility < 6%"] = df["Volatility"] < 0.06
    confirmations["Volume > SMA20"] = df["Volume"] > df["Volume_SMA20"]
    confirmations["ADX > 25"] = df["ADX"] > 25
    confirmations["Price > EMA50"] = close > df["EMA50"]
    confirmations["Price > EMA200"] = close > df["EMA200"]
    confirmations["MACD > Signal"] = df["MACD"] > df["MACD_Signal"]

    for column in CONFIRMATION_COLUMNS:
        df[column] = confirmations[column].fillna(False)
    df["Confirmation_Count"] = confirmations.fillna(False).sum(axis=1).astype(int)
    df["Indicator_Ready"] = (
        (np.arange(len(df)) >= 199)
        & df[["RSI", "Momentum", "Volatility", "Volume_SMA20", "ADX", "EMA50", "EMA200", "MACD_Signal"]]
        .notna()
        .all(axis=1)
    )
    df.loc[~df["Indicator_Ready"], "Confirmation_Count"] = 0
    return df

