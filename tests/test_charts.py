from __future__ import annotations

import pandas as pd

from charts import _regime_spans


def test_regime_spans_supports_arrow_string_dtype() -> None:
    index = pd.date_range("2026-01-01", periods=4, freq="h", tz="UTC")
    frame = pd.DataFrame(
        {"Regime": pd.Series(["Neutral 1", "Bull Run", "Bull Run", "Bear / Crash"], dtype="string[pyarrow]").array},
        index=index,
    )

    spans = list(_regime_spans(frame))

    assert spans == [
        (index[0], index[0], "Neutral 1"),
        (index[1], index[2], "Bull Run"),
        (index[3], index[3], "Bear / Crash"),
    ]
