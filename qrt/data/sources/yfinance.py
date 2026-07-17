"""Yahoo Finance market data source (stocks, ETFs, indices).

    ohlc = q.data.sources.yfinance.read("AAPL", "2024-01-01", "2025-01-01", "1d")
"""

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

from qrt.data.sources._util import (
    DEFAULT_CACHE_DIR,
    cached,
    no_data_error,
    normalize_range,
    read_many,
)


def read(
    symbols: str | list[str],
    start_date: str | datetime,
    end_date: str | datetime,
    time_interval: str = "1D",
    cache_dir: str | Path = DEFAULT_CACHE_DIR,
) -> pd.DataFrame | dict[str, pd.DataFrame]:
    """Fetch OHLCV bars from Yahoo Finance (cached locally as parquet).

    Fetched data is cached as parquet files named like
    ``{symbol}-{interval}-{start}-{end}.parquet`` under ``cache_dir``, so
    repeated requests for the same range don't hit the network. Only
    intervals supported by Yahoo are available (e.g. ``1m, 5m, 1h, 1D``);
    intraday data is limited to recent history by Yahoo.

    Args:
        symbols: A single symbol, or a list of symbols.
        start_date: Start date (inclusive), ``YYYY-MM-DD`` or datetime.
        end_date: End date (inclusive), ``YYYY-MM-DD`` or datetime.
        time_interval: Pandas offset alias (e.g. ``"1h"``, ``"5min"``, ``"1D"``).
        cache_dir: Directory for parquet OHLC caches.

    Returns:
        A single DataFrame if ``symbols`` is a string, otherwise a dict of
        DataFrames keyed by symbol (failed symbols are skipped with a
        warning, with a progress bar shown).
    """
    cache_dir = Path(cache_dir)
    if isinstance(symbols, str):
        return _read_one(symbols, start_date, end_date, time_interval, cache_dir)
    return read_many(
        symbols,
        lambda s: _read_one(s, start_date, end_date, time_interval, cache_dir),
        desc="Fetching OHLC (yfinance)",
    )


def _read_one(
    symbol: str,
    start_date: str | datetime,
    end_date: str | datetime,
    time_interval: str,
    cache_dir: Path,
) -> pd.DataFrame:
    """Fetch OHLCV bars for a single symbol (cached as parquet)."""
    start, end = normalize_range(start_date, end_date)
    interval = _to_yahoo_interval(time_interval)
    cache_path = cache_dir / f"{symbol}-{interval}-{start:%Y-%m-%d}-{end:%Y-%m-%d}.parquet"
    return cached(
        cache_path,
        lambda: _download(symbol, start, end, interval),
        index="datetime",
    )


def _download(
    symbol: str, start: datetime, end: datetime, interval: str
) -> pd.DataFrame:
    """Download and normalize OHLCV bars from Yahoo."""
    df = yf.download(
        symbol,
        start=start,
        # yfinance treats `end` as exclusive; our contract is inclusive.
        end=end + timedelta(days=1),
        interval=interval,
        progress=False,
        auto_adjust=True,
        multi_level_index=False,
        timeout=30,
    )
    if df is None or df.empty:
        raise no_data_error(symbol, start, end)

    df = df.rename(columns=str.lower)
    df.index.name = "datetime"
    cols = [c for c in ("open", "high", "low", "close", "volume") if c in df.columns]
    return df[cols]


def _to_yahoo_interval(time_interval: str) -> str:
    """Map common pandas offset aliases to Yahoo interval strings."""
    mapping = {
        "1min": "1m",
        "5min": "5m",
        "15min": "15m",
        "30min": "30m",
        "1h": "1h",
        "1D": "1d",
        "1d": "1d",
        "1W": "1wk",
        "1M": "1mo",
    }
    return mapping.get(time_interval, time_interval)
