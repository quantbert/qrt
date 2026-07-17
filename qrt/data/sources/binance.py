"""Binance futures market data source.

Downloads daily tick-level trade dumps from ``data.binance.vision`` and
caches them locally as parquet. OHLC bars are aggregated from trades.

    ohlc = q.data.sources.binance.read("BTCUSDT", "2025-01-01", "2025-01-07", "1h")
"""

import logging
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

from qrt.data.sources._util import (
    DEFAULT_CACHE_DIR,
    cached,
    no_data_error,
    normalize_date,
    normalize_range,
    read_many,
    trades_to_ohlc,
)

logger = logging.getLogger(__name__)

_BASE_URL = "https://data.binance.vision/data/futures/um/daily/trades"

_TRADE_DTYPES = {
    "id": "int64",
    "price": "float64",
    "qty": "float64",
    "quote_qty": "float64",
    "time": "int64",
    "is_buyer_maker": "bool",
}


def fetch_trades_day(
    symbol: str,
    date: str | datetime,
    download_dir: str | Path = "data",
    cache_dir: str | Path = DEFAULT_CACHE_DIR,
) -> pd.DataFrame:
    """Fetch all trades for ``symbol`` on a single day (cached as parquet).

    Args:
        symbol: Binance symbol, e.g. ``"BTCUSDT"``.
        date: Day to fetch, ``YYYY-MM-DD`` or datetime.
        download_dir: Directory for temporary zip/csv downloads.
        cache_dir: Directory for parquet trade caches.

    Returns:
        DataFrame with columns ``id, price, qty, quote_qty, time,
        is_buyer_maker, datetime``.
    """
    download_dir, cache_dir = Path(download_dir), Path(cache_dir)
    date_str = f"{normalize_date(date):%Y-%m-%d}"
    cache_path = cache_dir / f"{symbol}-trades-{date_str}.parquet"
    return cached(cache_path, lambda: _fetch_trades_csv(symbol, date_str, download_dir))


def _fetch_trades_csv(symbol: str, date_str: str, download_dir: Path) -> pd.DataFrame:
    """Download, unzip, and parse one day of trades."""
    csv_path = _download_and_unzip(symbol, date_str, download_dir)
    try:
        df = pd.read_csv(csv_path, dtype=_TRADE_DTYPES)
        df["datetime"] = pd.to_datetime(df["time"], unit="ms")
    finally:
        csv_path.unlink(missing_ok=True)
    return df


def fetch_trades(
    symbol: str,
    start_date: str | datetime,
    end_date: str | datetime,
    download_dir: str | Path = "data",
    cache_dir: str | Path = DEFAULT_CACHE_DIR,
) -> pd.DataFrame:
    """Fetch trades for a date range (inclusive), concatenated.

    Days that fail to download are skipped with a warning.
    """
    download_dir, cache_dir = Path(download_dir), Path(cache_dir)
    frames = list(_iter_days(symbol, start_date, end_date, download_dir, cache_dir))
    if not frames:
        raise no_data_error(symbol, start_date, end_date)
    return pd.concat(frames, ignore_index=True)


def read(
    symbols: str | list[str],
    start_date: str | datetime,
    end_date: str | datetime,
    time_interval: str = "1h",
    download_dir: str | Path = "data",
    cache_dir: str | Path = DEFAULT_CACHE_DIR,
) -> pd.DataFrame | dict[str, pd.DataFrame]:
    """Fetch OHLCV bars aggregated from tick trades.

    Bars are aggregated per day and concatenated, so intervals should
    divide evenly into one day.

    Args:
        symbols: A single symbol, or a list of symbols.
        start_date: Start date (inclusive), ``YYYY-MM-DD`` or datetime.
        end_date: End date (inclusive), ``YYYY-MM-DD`` or datetime.
        time_interval: Pandas offset alias (e.g. ``"1h"``, ``"5min"``).
        download_dir: Directory for temporary zip/csv downloads.
        cache_dir: Directory for parquet trade caches.

    Returns:
        A single DataFrame if ``symbols`` is a string, otherwise a dict of
        DataFrames keyed by symbol (failed symbols are skipped with a
        warning, with a progress bar shown).
    """
    download_dir, cache_dir = Path(download_dir), Path(cache_dir)
    if isinstance(symbols, str):
        return _read_one(symbols, start_date, end_date, time_interval, download_dir, cache_dir)
    return read_many(
        symbols,
        lambda s: _read_one(s, start_date, end_date, time_interval, download_dir, cache_dir),
        desc="Fetching OHLC (binance)",
    )


def _read_one(
    symbol: str,
    start_date: str | datetime,
    end_date: str | datetime,
    time_interval: str,
    download_dir: Path,
    cache_dir: Path,
) -> pd.DataFrame:
    bars = [
        trades_to_ohlc(day_trades, time_interval)
        for day_trades in _iter_days(symbol, start_date, end_date, download_dir, cache_dir)
    ]
    if not bars:
        raise no_data_error(symbol, start_date, end_date)
    return pd.concat(bars).sort_index()


def _iter_days(
    symbol: str,
    start_date: str | datetime,
    end_date: str | datetime,
    download_dir: Path,
    cache_dir: Path,
):
    """Yield per-day trade DataFrames over a range, skipping failures."""
    start, end = normalize_range(start_date, end_date)

    num_days = (end - start).days + 1
    for i in tqdm(range(num_days), desc=f"Downloading {symbol}"):
        day = start + timedelta(days=i)
        try:
            yield fetch_trades_day(symbol, day, download_dir, cache_dir)
        except Exception as e:  # noqa: BLE001 - skip bad days, keep going
            logger.warning("%s %s: %s", symbol, f"{day:%Y-%m-%d}", e)


def _download_and_unzip(symbol: str, date_str: str, download_dir: Path) -> Path:
    """Download the daily zip and extract the csv; return the csv path."""
    download_dir.mkdir(parents=True, exist_ok=True)
    zip_path = download_dir / f"{symbol}-trades-{date_str}.zip"
    url = f"{_BASE_URL}/{symbol}/{symbol}-trades-{date_str}.zip"

    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))
        with (
            open(zip_path, "wb") as f,
            tqdm(
                total=total,
                unit="B",
                unit_scale=True,
                desc=zip_path.name,
                leave=False,
            ) as bar,
        ):
            for chunk in response.iter_content(chunk_size=1 << 20):
                f.write(chunk)
                bar.update(len(chunk))
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(download_dir)
    finally:
        zip_path.unlink(missing_ok=True)

    return download_dir / f"{symbol}-trades-{date_str}.csv"
