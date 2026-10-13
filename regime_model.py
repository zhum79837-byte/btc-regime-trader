"""Seven-state Gaussian HMM with causal walk-forward regime inference."""

from __future__ import annotations

from dataclasses import dataclass
import warnings

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler

from config import CONFIG


FEATURE_COLUMNS = ["Returns", "Range", "Volume_Volatility"]


@dataclass
class RegimeResult:
    frame: pd.DataFrame
    state_statistics: pd.DataFrame
    bull_state: int
    bear_state: int
    model: GaussianHMM
    scaler: StandardScaler


@dataclass
class WalkForwardRegimeResult(RegimeResult):
    evaluation_start: pd.Timestamp
    current_state: int
    current_regime: str
    current_model_trained_through: pd.Timestamp
    current_observation_time: pd.Timestamp
    retrain_count: int


def _new_model() -> GaussianHMM:
    return GaussianHMM(
        n_components=CONFIG.hmm_components,
        covariance_type="diag",
        n_iter=CONFIG.hmm_iterations,
        random_state=CONFIG.hmm_random_state,
        min_covar=1e-5,
    )


def _fit_bundle(valid: pd.DataFrame):
    minimum_rows = max(500, CONFIG.hmm_components * 20)
    if len(valid) < minimum_rows:
        raise ValueError(f"At least {minimum_rows} valid hourly rows are required for the HMM; got {len(valid)}")

    scaler = StandardScaler()
    features = scaler.fit_transform(valid[FEATURE_COLUMNS])
    model = _new_model()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Model is not converging")
        model.fit(features)
    states = model.predict(features)
    stats = (
        valid.assign(State=states)
        .groupby("State")
        .agg(
            Mean_Return=("Returns", "mean"),
            Mean_Range=("Range", "mean"),
            Observations=("Returns", "size"),
        )
        .reindex(range(CONFIG.hmm_components))
    )
    present = stats.dropna(subset=["Mean_Return"])
    if present.empty:
        raise ValueError("The fitted HMM produced no classifiable states")
    bull_state = int(present["Mean_Return"].idxmax())
    bear_state = int(present["Mean_Return"].idxmin())
    stats["Label"] = [_state_label(state, bull_state, bear_state) for state in stats.index]
    stats.index.name = "State"
    return model, scaler, stats, bull_state, bear_state


def _state_label(state: int, bull_state: int, bear_state: int) -> str:
    if state == bull_state:
        return "Bull Run"
    if state == bear_state:
        return "Bear / Crash"
    return f"Neutral {state}"


def _logsumexp(values: np.ndarray, axis: int) -> np.ndarray:
    maximum = np.max(values, axis=axis, keepdims=True)
    summed = np.sum(np.exp(values - maximum), axis=axis, keepdims=True)
    return np.squeeze(maximum + np.log(summed), axis=axis)


def _emission_log_likelihood(model: GaussianHMM, features: np.ndarray) -> np.ndarray:
    """Gaussian diagonal-covariance log likelihood without future smoothing."""
    covars = np.asarray(model._covars_, dtype=float)  # hmmlearn stores diagonal variances here.
    covars = np.maximum(covars, 1e-12)
    differences = features[:, None, :] - model.means_[None, :, :]
    normalizer = np.sum(np.log(2 * np.pi * covars), axis=1)
    distance = np.sum(differences**2 / covars[None, :, :], axis=2)
    return -0.5 * (normalizer[None, :] + distance)


def _causal_states(
    model: GaussianHMM,
    training_features: np.ndarray,
    observation_features: np.ndarray,
) -> np.ndarray:
    """Filter states forward so each prediction uses no future observations."""
    log_start = np.log(np.maximum(model.startprob_, 1e-300))
    log_transition = np.log(np.maximum(model.transmat_, 1e-300))
    training_emissions = _emission_log_likelihood(model, training_features)

    alpha = log_start + training_emissions[0]
    alpha -= _logsumexp(alpha[None, :], axis=1)[0]
    for emission in training_emissions[1:]:
        alpha = _logsumexp(alpha[:, None] + log_transition, axis=0) + emission
        alpha -= _logsumexp(alpha[None, :], axis=1)[0]

    predicted: list[int] = []
    for emission in _emission_log_likelihood(model, observation_features):
        alpha = _logsumexp(alpha[:, None] + log_transition, axis=0) + emission
        alpha -= _logsumexp(alpha[None, :], axis=1)[0]
        predicted.append(int(np.argmax(alpha)))
    return np.asarray(predicted, dtype=int)


def _valid_features(data: pd.DataFrame) -> pd.DataFrame:
    missing = set(FEATURE_COLUMNS) - set(data.columns)
    if missing:
        raise ValueError(f"Missing HMM features: {sorted(missing)}")
    return data[FEATURE_COLUMNS].replace([np.inf, -np.inf], np.nan).dropna()


def fit_regime_model(data: pd.DataFrame) -> RegimeResult:
    """Fit one in-sample HMM. Retained for diagnostics and unit tests."""
    frame = data.copy()
    valid = _valid_features(frame)
    model, scaler, stats, bull_state, bear_state = _fit_bundle(valid)
    states = model.predict(scaler.transform(valid[FEATURE_COLUMNS]))

    frame["State"] = pd.Series(pd.NA, index=frame.index, dtype="Int64")
    frame.loc[valid.index, "State"] = states
    frame["State"] = frame["State"].ffill().bfill().astype(int)
    frame["Regime"] = frame["State"].map(lambda state: _state_label(int(state), bull_state, bear_state))
    return RegimeResult(frame, stats, bull_state, bear_state, model, scaler)


def fit_walk_forward_regime_model(
    data: pd.DataFrame,
    training_rows: int = CONFIG.training_window_hours,
    retrain_rows: int = CONFIG.retrain_interval_hours,
) -> WalkForwardRegimeResult:
    """Run a rolling, causal walk-forward HMM evaluation.

    Every segment is predicted by a model fitted only on observations that
    existed before that segment. The current regime is the final causal
    prediction from the same model version that drives the backtest position.
    """
    if training_rows < 500:
        raise ValueError("training_rows must be at least 500")
    if retrain_rows < 1:
        raise ValueError("retrain_rows must be positive")

    source = data.copy().sort_index()
    valid = _valid_features(source)
    if len(valid) <= training_rows + 1:
        raise ValueError(
            f"Walk-forward evaluation needs more than {training_rows + 1} valid rows; got {len(valid)}"
        )

    state_series = pd.Series(pd.NA, index=source.index, dtype="Int64")
    regime_series = pd.Series(pd.NA, index=source.index, dtype="string")
    model_version = pd.Series(pd.NaT, index=source.index, dtype="datetime64[ns, UTC]")
    retrain_count = 0

    for segment_start in range(training_rows, len(valid), retrain_rows):
        segment_end = min(segment_start + retrain_rows, len(valid))
        training = valid.iloc[segment_start - training_rows : segment_start]
        observations = valid.iloc[segment_start:segment_end]
        model, scaler, stats, bull_state, bear_state = _fit_bundle(training)
        training_features = scaler.transform(training[FEATURE_COLUMNS])
        observation_features = scaler.transform(observations[FEATURE_COLUMNS])
        states = _causal_states(model, training_features, observation_features)
        labels = [_state_label(int(state), bull_state, bear_state) for state in states]
        state_series.loc[observations.index] = states
        regime_series.loc[observations.index] = labels
        model_version.loc[observations.index] = training.index[-1]
        retrain_count += 1

    evaluation_start = valid.index[training_rows]
    frame = source.loc[evaluation_start:].copy()
    frame["State"] = state_series.loc[frame.index].ffill()
    frame["Regime"] = regime_series.loc[frame.index].ffill()
    frame["Model_Train_End"] = model_version.loc[frame.index].ffill()
    frame = frame.dropna(subset=["State", "Regime"]).copy()
    frame["State"] = frame["State"].astype(int)

    current_observation_time = valid.index[-1]
    current_state = int(state_series.loc[current_observation_time])
    current_regime = str(regime_series.loc[current_observation_time])
    current_model_trained_through = pd.Timestamp(model_version.loc[current_observation_time])

    return WalkForwardRegimeResult(
        frame=frame,
        state_statistics=stats,
        bull_state=bull_state,
        bear_state=bear_state,
        model=model,
        scaler=scaler,
        evaluation_start=evaluation_start,
        current_state=current_state,
        current_regime=current_regime,
        current_model_trained_through=current_model_trained_through,
        current_observation_time=current_observation_time,
        retrain_count=retrain_count,
    )
