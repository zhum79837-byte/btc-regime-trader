from datetime import datetime, timezone

import pandas as pd

from data_loader import (
    _drop_incomplete_candles,
    _merge_locked_history,
    _save_immutable_snapshot,
)


def _bars(index, close_values):
    close = pd.Series(close_values, index=index, dtype=float)
    return pd.DataFrame(
        {
            "Open": close,
            "High": close + 1,
            "Low": close - 1,
            "Close": close,
            "Volume": 100.0,
        },
        index=index,
    )


def test_current_hour_is_excluded():
    index = pd.date_range("2026-10-07 08:00", periods=3, freq="h", tz="UTC")
    data = _bars(index, [100, 101, 102])
    result = _drop_incomplete_candles(
        data,
        "1h",
        now=datetime(2026, 10, 7, 10, 35, tzinfo=timezone.utc),
    )
    assert result.index.tolist() == [index[0], index[1]]


def test_locked_history_preserves_old_values_and_only_appends_new_rows():
    old_index = pd.date_range("2026-10-07 08:00", periods=2, freq="h", tz="UTC")
    new_index = pd.date_range("2026-10-07 08:00", periods=3, freq="h", tz="UTC")
    cached = _bars(old_index, [100, 101])
    downloaded = _bars(new_index, [999, 998, 102])
    result = _merge_locked_history(cached, downloaded)
    assert result["Close"].tolist() == [100, 101, 102]


def test_snapshot_is_content_addressed_and_not_duplicated(tmp_path):
    index = pd.date_range("2026-10-07 08:00", periods=2, freq="h", tz="UTC")
    data = _bars(index, [100, 101])
    first = _save_immutable_snapshot(data, tmp_path)
    second = _save_immutable_snapshot(data, tmp_path)
    assert first == second
    assert first.exists()
    assert first.with_suffix(".sha256").exists()
    assert len(list(tmp_path.glob("*.parquet"))) == 1
