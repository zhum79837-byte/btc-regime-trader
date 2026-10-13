import numpy as np
import pandas as pd

from regime_model import fit_regime_model, fit_walk_forward_regime_model


def test_hmm_uses_seven_states_and_labels_extremes():
    rng = np.random.default_rng(7)
    blocks = []
    for state in range(7):
        rows = 120
        blocks.append(
            pd.DataFrame(
                {
                    "Returns": rng.normal((state - 3) * 0.0015, 0.0002, rows),
                    "Range": rng.normal(0.01 + state * 0.002, 0.0003, rows),
                    "Volume_Volatility": rng.normal(0.05 + state * 0.01, 0.002, rows),
                }
            )
        )
    frame = pd.concat(blocks, ignore_index=True)
    frame.index = pd.date_range("2025-01-01", periods=len(frame), freq="h", tz="UTC")
    result = fit_regime_model(frame)
    assert result.model.n_components == 7
    present = result.state_statistics.dropna(subset=["Mean_Return"])
    assert result.bull_state == present["Mean_Return"].idxmax()
    assert result.bear_state == present["Mean_Return"].idxmin()
    assert set(result.frame["Regime"]).issuperset({"Bull Run", "Bear / Crash"})


def test_walk_forward_prefix_does_not_change_when_future_rows_are_appended():
    rng = np.random.default_rng(19)
    rows = 1_050
    latent = (np.arange(rows) // 24) % 7
    frame = pd.DataFrame(
        {
            "Returns": rng.normal((latent - 3) * 0.001, 0.0004),
            "Range": rng.normal(0.01 + latent * 0.0015, 0.0005),
            "Volume_Volatility": rng.normal(0.05 + latent * 0.008, 0.003),
        },
        index=pd.date_range("2025-01-01", periods=rows, freq="h", tz="UTC"),
    )
    shorter = fit_walk_forward_regime_model(frame.iloc[:950], training_rows=500, retrain_rows=200)
    longer = fit_walk_forward_regime_model(frame, training_rows=500, retrain_rows=200)
    common = shorter.frame.index.intersection(longer.frame.index)
    pd.testing.assert_series_equal(
        shorter.frame.loc[common, "State"],
        longer.frame.loc[common, "State"],
    )
    pd.testing.assert_series_equal(
        shorter.frame.loc[common, "Regime"],
        longer.frame.loc[common, "Regime"],
    )
    assert longer.current_state == int(longer.frame["State"].iloc[-1])
    assert longer.current_regime == str(longer.frame["Regime"].iloc[-1])
    assert longer.current_model_trained_through == longer.frame["Model_Train_End"].iloc[-1]

