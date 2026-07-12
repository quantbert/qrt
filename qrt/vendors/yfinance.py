"""Yahoo Finance market data vendor (stocks, ETFs, indices)."""

import logging
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from qrt.vendors.base import DataVendor, _no_data_error, _normalize_range

logger = logging.getLogger(__name__)


class YFinanceVendor(DataVendor):
    """Vendor backed by the ``yfinance`` package.

    Fetched OHLC data is cached locally as parquet files named like
    ``{symbol}-{interval}-{start}-{end}.parquet`` so repeated requests
    for the same range don't hit the network.

    Args:
        cache_dir: Directory for parquet OHLC caches.
    """

    name = "yfinance"

    def fetch_ohlc(
        self,
        symbol: str,
        start_date: str | datetime,
        end_date: str | datetime,
        time_interval: str = "1D",
    ) -> pd.DataFrame:
        """Fetch OHLCV bars from Yahoo Finance (cached as parquet).

        See :meth:`DataVendor.fetch_ohlc`. Only intervals supported by
        Yahoo are available (e.g. ``1m, 5m, 1h, 1D``); intraday data is
        limited to recent history by Yahoo.
        """
        start, end = _normalize_range(start_date, end_date)
        interval = _to_yahoo_interval(time_interval)
        cache_path = self.cache_dir / (
            f"{symbol}-{interval}-{start:%Y-%m-%d}-{end:%Y-%m-%d}.parquet"
        )
        return self._cached(
            cache_path,
            lambda: self._download(symbol, start, end, interval),
            index="datetime",
        )

    def _download(
        self, symbol: str, start: datetime, end: datetime, interval: str
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
            raise _no_data_error(symbol, start, end)

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
