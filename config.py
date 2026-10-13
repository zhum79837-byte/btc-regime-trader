"""Central configuration for the standalone BTC regime application."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    ticker: str = "BTC-USD"
    period: str = "730d"
    interval: str = "1h"
    hmm_components: int = 7
    hmm_iterations: int = 100
    hmm_random_state: int = 42
    training_window_hours: int = 24 * 180
    retrain_interval_hours: int = 24 * 30
    initial_capital: float = 10_000.0
    leverage: float = 2.5
    cooldown_hours: int = 48
    required_confirmations: int = 7
    volume_volatility_window: int = 24


CONFIG = AppConfig()

