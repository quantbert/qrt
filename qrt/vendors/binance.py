"""Binance futures market data vendor.

Downloads daily tick-level trade dumps from ``data.binance.vision`` and
caches them locally as parquet. OHLC bars are aggregated from trades.
"""

import logging
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

from qrt.vendors.base import (
    DEFAULT_CACHE_DIR,
    DataVendor,
    _no_data_error,
    _normalize_date,
    _normalize_range,
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


class BinanceVendor(DataVendor):
    """Vendor for Binance USD-M futures daily trade dumps.

    Args:
        download_dir: Directory for temporary zip/csv downloads.
        cache_dir: Directory for parquet trade caches.
    """

    name = "binance"

    def __init__(
        self,
        download_dir: str | Path = "data",
        cache_dir: str | Path = DEFAULT_CACHE_DIR,
    ) -> None:
        super().__init__(cache_dir)
        self.download_dir = Path(download_dir)

    def fetch_trades_day(self, symbol: str, date: str | datetime) -> pd.DataFrame:
        """Fetch all trades for ``symbol`` on a single day (cached as parquet).

        Args:
            symbol: Binance symbol, e.g. ``"BTCUSDT"``.
            date: Day to fetch, ``YYYY-MM-DD`` or datetime.

        Returns:
            DataFrame with columns ``id, price, qty, quote_qty, time,
            is_buyer_maker, datetime``.
        """
        date_str = f"{_normalize_date(date):%Y-%m-%d}"
        cache_path = self.cache_dir / f"{symbol}-trades-{date_str}.parquet"
        return self._cached(cache_path, lambda: self._fetch_trades_csv(symbol, date_str))

    def _fetch_trades_csv(self, symbol: str, date_str: str) -> pd.DataFrame:
        """Download, unzip, and parse one day of trades."""
        csv_path = self._download_and_unzip(symbol, date_str)
        try:
            df = pd.read_csv(csv_path, dtype=_TRADE_DTYPES)
            df["datetime"] = pd.to_datetime(df["time"], unit="ms")
        finally:
            csv_path.unlink(missing_ok=True)
        return df

    def fetch_trades(
        self,
        symbol: str,
        start_date: str | datetime,
        end_date: str | datetime,
    ) -> pd.DataFrame:
        """Fetch trades for a date range (inclusive), concatenated.

        Days that fail to download are skipped with a warning.
        """
        frames = list(self._iter_days(symbol, start_date, end_date))
        if not frames:
            raise _no_data_error(symbol, start_date, end_date)
        return pd.concat(frames, ignore_index=True)

    def fetch_ohlc(
        self,
        symbol: str,
        start_date: str | datetime,
        end_date: str | datetime,
        time_interval: str = "1h",
    ) -> pd.DataFrame:
        """Fetch OHLCV bars aggregated from tick trades.

        See :meth:`DataVendor.fetch_ohlc`. Bars are aggregated per day and
        concatenated, so intervals should divide evenly into one day.
        """
        bars = [
            trades_to_ohlc(day_trades, time_interval)
            for day_trades in self._iter_days(symbol, start_date, end_date)
        ]
        if not bars:
            raise _no_data_error(symbol, start_date, end_date)
        return pd.concat(bars).sort_index()

    def _iter_days(
        self, symbol: str, start_date: str | datetime, end_date: str | datetime
    ):
        """Yield per-day trade DataFrames over a range, skipping failures."""
        start, end = _normalize_range(start_date, end_date)

        num_days = (end - start).days + 1
        for i in tqdm(range(num_days), desc=f"Downloading {symbol}"):
            day = start + timedelta(days=i)
            try:
                yield self.fetch_trades_day(symbol, day)
            except Exception as e:  # noqa: BLE001 - skip bad days, keep going
                logger.warning("%s %s: %s", symbol, f"{day:%Y-%m-%d}", e)

    def _download_and_unzip(self, symbol: str, date_str: str) -> Path:
        """Download the daily zip and extract the csv; return the csv path."""
        self.download_dir.mkdir(parents=True, exist_ok=True)
        zip_path = self.download_dir / f"{symbol}-trades-{date_str}.zip"
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
                zf.extractall(self.download_dir)
        finally:
            zip_path.unlink(missing_ok=True)

        return self.download_dir / f"{symbol}-trades-{date_str}.csv"
