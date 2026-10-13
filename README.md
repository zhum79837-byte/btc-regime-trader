# BTC Regime Trader

[简体中文说明](README.zh-CN.md)

A standalone research and backtesting dashboard for `BTC-USD`. It is intentionally independent from every other project under `D:\code` and has no exchange or order-execution integration.

The sidebar language control switches the complete dashboard between Simplified Chinese and the original English version. The selection is also reflected in the URL (`?language=zh` or `?language=en`), so either version can be bookmarked directly.

## Model and strategy

- Seven-state diagonal-covariance `hmmlearn.GaussianHMM` trained on hourly returns, `(High - Low) / Close`, and 24-hour volume-change volatility.
- The backtest uses a causal walk-forward process: each model sees only the previous 180 days and is retrained every 30 days. Future candles never revise an earlier decision.
- The active model advances on the same 30-day walk-forward schedule and always uses the trailing 180 days, so learning continues without fixed calendar start and end dates.
- The hidden state with the highest average return is labeled **Bull Run**; the state with the lowest is labeled **Bear / Crash**.
- Long entry requires the Bull Run state plus at least seven of eight confirmations.
- Any Bear / Crash state exits the position. Every exit starts a 48-hour no-entry cooldown.
- Returns and equity simulate 2.5x exposure on $10,000 initial capital.

## Run on Windows

1. Double-click `setup.bat` once.
2. Double-click `run_app.bat` thereafter.
3. Stop the app by closing the terminal window or pressing `Ctrl+C` in it.

The first run downloads data and writes `data/btc_usd_1h.parquet`. Refreshes append newly completed hourly candles without rewriting already locked history. Each changed dataset also creates a content-addressed, write-once snapshot under `data/snapshots/`. The current unfinished hourly candle is excluded. If the network is unavailable, the latest valid cache is used.

## Command line

```powershell
cd D:\code\btc-regime-trader
.\setup.bat
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run an end-to-end console validation:

```powershell
.\.venv\Scripts\python.exe validate.py
```

## Methodology notes

- A signal is confirmed at an hourly close and its simulated fill occurs at the next hourly open. Fees, funding, spread, and slippage are excluded.
- Historical metrics are out-of-sample walk-forward results, not an HMM trained on the complete history it is evaluating.
- The displayed regime, simulated position, and next action all come from the same active walk-forward model version. Its training cutoff and latest classified candle are shown on the page.
- `Volatility < 6%` means trailing 24-hour realized volatility: the square root of summed squared hourly returns.
- `Volume Volatility` means the rolling 24-hour standard deviation of changes in `log1p(volume)`, which safely handles Yahoo candles with zero reported volume.
- The first 200 hours are an indicator warm-up period and cannot open a trade.
- An open trade at the end remains open; dashboard equity includes its unrealized leveraged PnL, while win rate counts closed trades only.
- This is research software, not financial advice and not a live trading robot.
