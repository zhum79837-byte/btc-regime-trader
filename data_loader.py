"""Market-data loading and local caching for BTC-USD hourly candles."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path

import pandas as pd
import yfinance as yf

from config import CONFIG


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CACHE_PATH = PROJECT_ROOT / "data" / "btc_usd_1h.parquet"
DEFAULT_SNAPSHOT_DIR = PROJECT_ROOT / "data" / "snapshots"
REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


class MarketDataError(RuntimeError):
    """Raised when usable market data cannot be downloaded or loaded."""


def _normalise_download(raw: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if raw is None or raw.empty:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    data = raw.copy()
    if isinstance(data.columns, pd.MultiIndex):
        # yfinance may return either (price, ticker) or (ticker, price).
        if ticker in data.columns.get_level_values(-1):
            data = data.xs(ticker, axis=1, level=-1)
        elif ticker in data.columns.get_level_values(0):
            data = data.xs(ticker, axis=1, level=0)
        else:
            data.columns = data.columns.get_level_values(0)

    missing = set(REQUIRED_COLUMNS) - set(data.columns)
    if missing:
        raise MarketDataError(f"Downloaded data is missing columns: {sorted(missing)}")

    data = data[REQUIRED_COLUMNS].copy()
    data.index = pd.to_datetime(data.index, utc=True)
    data.index.name = "Datetime"
    data = data[~data.index.duplicated(keep="last")].sort_index()
    data = data.apply(pd.to_numeric, errors="coerce")
    data = data.dropna(subset=["Open", "High", "Low", "Close"])
    return data[data["Close"] > 0]


def _drop_incomplete_candles(
    data: pd.DataFrame,
    interval: str,
    now: datetime | pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Remove the currently forming candle from intraday data."""
    if data.empty or interval not in {"1h", "60m"}:
        return data.copy()
    current_time = pd.Timestamp(now if now is not None else datetime.now(timezone.utc))
    if current_time.tzinfo is None:
        current_time = current_time.tz_localize("UTC")
    else:
        current_time = current_time.tz_convert("UTC")
    current_hour = current_time.floor("h")
    return data.loc[data.index < current_hour].copy()


def _frame_digest(data: pd.DataFrame) -> str:
    hashed = pd.util.hash_pandas_object(data[REQUIRED_COLUMNS], index=True).values.tobytes()
    return hashlib.sha256(hashed).hexdigest()


def _merge_locked_history(cached: pd.DataFrame | None, downloaded: pd.DataFrame) -> pd.DataFrame:
    """Append unseen closed candles while preserving all cached OHLCV values."""
    if cached is None or cached.empty:
        return downloaded.copy()
    additions = downloaded.loc[~downloaded.index.isin(cached.index)]
    return pd.concat([cached, additions]).sort_index()


def _save_immutable_snapshot(data: pd.DataFrame, snapshot_dir: Path) -> Path:
    """Save a content-addressed snapshot without overwriting older snapshots."""
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    digest = _frame_digest(data)
    through = data.index[-1].strftime("%Y%m%dT%H%M%SZ")
    snapshot_path = snapshot_dir / f"btc_usd_1h_through_{through}_{digest[:12]}.parquet"
    if not snapshot_path.exists():
        data.to_parquet(snapshot_path)
        snapshot_path.with_suffix(".sha256").write_text(f"{digest}\n", encoding="ascii")
    return snapshot_path


def latest_snapshot_path(snapshot_dir: Path | str = DEFAULT_SNAPSHOT_DIR) -> Path | None:
    snapshots = list(Path(snapshot_dir).glob("*.parquet"))
    return max(snapshots, key=lambda path: path.stat().st_mtime) if snapshots else None


def _download_full_period(ticker: str, period: str, interval: str) -> pd.DataFrame:
    raw = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=False,
        actions=False,
        progress=False,
        threads=False,
        timeout=30,
        multi_level_index=False,
    )
    return _normalise_download(raw, ticker)


def _download_in_chunks(
    ticker: str,
    days: int = 730,
    interval: str = "1h",
    chunk_days: int = 59,
) -> pd.DataFrame:
    """Fallback for Yahoo endpoints that restrict intraday requests per call."""
    end = datetime.now(timezone.utc) + timedelta(hours=1)
    start = end - timedelta(days=days)
    chunks: list[pd.DataFrame] = []

    cursor = start
    while cursor < end:
        chunk_end = min(cursor + timedelta(days=chunk_days), end)
        raw = yf.download(
            ticker,
            start=cursor,
            end=chunk_end,
            interval=interval,
            auto_adjust=False,
            actions=False,
            progress=False,
            threads=False,
            timeout=30,
            multi_level_index=False,
        )
        chunk = _normalise_download(raw, ticker)
        if not chunk.empty:
            chunks.append(chunk)
        cursor = chunk_end

    if not chunks:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    return _normalise_download(pd.concat(chunks), ticker)


def load_market_data(
    ticker: str = CONFIG.ticker,
    period: str = CONFIG.period,
    interval: str = CONFIG.interval,
    cache_path: Path | str = DEFAULT_CACHE_PATH,
    snapshot_dir: Path | str = DEFAULT_SNAPSHOT_DIR,
    force_refresh: bool = False,
    cache_max_age_hours: int = 1,
) -> pd.DataFrame:
    """Load BTC candles from cache or Yahoo Finance.

    A direct 730-day hourly request is attempted first. If Yahoo rejects that
    range, 59-day requests are attempted and joined. A valid cache remains a
    fallback during temporary network/provider failures.
    """
    cache_path = Path(cache_path)
    snapshot_dir = Path(snapshot_dir)
    cached: pd.DataFrame | None = None
    if cache_path.exists():
        cached = _normalise_download(pd.read_parquet(cache_path), ticker)
        cached = _drop_incomplete_candles(cached, interval)
        modified = datetime.fromtimestamp(cache_path.stat().st_mtime, tz=timezone.utc)
        if not force_refresh and datetime.now(timezone.utc) - modified < timedelta(hours=cache_max_age_hours):
            return cached

    errors: list[str] = []
    data = pd.DataFrame()
    try:
        data = _download_full_period(ticker, period, interval)
    except Exception as exc:  # provider/network exceptions vary by yfinance release
        errors.append(f"full-period request: {exc}")

    if data.empty:
        try:
            data = _download_in_chunks(ticker, days=730, interval=interval)
        except Exception as exc:
            errors.append(f"chunked request: {exc}")

    if not data.empty:
        data = _drop_incomplete_candles(data, interval)
        data = _merge_locked_history(cached, data)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        data.to_parquet(cache_path)
        _save_immutable_snapshot(data, snapshot_dir)
        return data

    if cached is not None and not cached.empty:
        return cached

    details = "; ".join(errors) if errors else "Yahoo Finance returned no rows"
    raise MarketDataError(
        "Unable to load BTC-USD hourly data. Yahoo may be rate-limiting or "
        f"restricting historical intraday requests. Details: {details}"
    )

