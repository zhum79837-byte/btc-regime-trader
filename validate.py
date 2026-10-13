"""Run a concise end-to-end validation against the cached/live data."""

from backtester import run_backtest
from data_loader import load_market_data
from indicators import calculate_indicators
from regime_model import FEATURE_COLUMNS, fit_walk_forward_regime_model


def main() -> None:
    data = load_market_data()
    enriched = calculate_indicators(data)
    regimes = fit_walk_forward_regime_model(enriched)
    result = run_backtest(regimes.frame)
    latest = result.frame.iloc[-1]

    print(f"Candles: {len(data):,} ({data.index[0]} to {data.index[-1]})")
    print(f"Valid HMM rows: {len(enriched[FEATURE_COLUMNS].dropna()):,}")
    print(f"Bull state: {regimes.bull_state}; Bear / Crash state: {regimes.bear_state}")
    print(
        f"Walk-forward: train {regimes.evaluation_start - enriched.index[0]} before evaluation; "
        f"{regimes.retrain_count} historical retrains"
    )
    print(
        f"Current: {result.current_position} / {regimes.current_regime} / "
        f"{int(latest['Confirmation_Count'])}/8"
    )
    print(f"Current model trained through: {regimes.current_model_trained_through}")
    print(f"Closed trades: {len(result.trades)}")
    for name in ["Total Return", "Alpha vs Buy & Hold", "Win Rate", "Max Drawdown"]:
        print(f"{name}: {result.metrics[name]:.2%}")


if __name__ == "__main__":
    main()
