import numpy as np
import pandas as pd

from indicators import CONFIRMATION_COLUMNS, calculate_indicators


def test_calculates_all_indicators_and_votes():
    index = pd.date_range("2025-01-01", periods=300, freq="h", tz="UTC")
    close = pd.Series(np.linspace(100, 160, len(index)) + np.sin(np.arange(len(index)) / 5), index=index)
    data = pd.DataFrame(
        {
            "Open": close.shift().fillna(close.iloc[0]),
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": 1_000 + (np.arange(len(index)) % 24) * 20,
        },
        index=index,
    )
    result = calculate_indicators(data)
    assert all(column in result for column in CONFIRMATION_COLUMNS)
    assert result["Confirmation_Count"].between(0, 8).all()
    assert {"Returns", "Range", "Volume_Volatility", "ADX"}.issubset(result.columns)

