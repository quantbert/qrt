"""Common interface for market data vendors."""

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd
from tqdm import tqdm

logger = logging.getLogger(__name__)

#: Default directory for parquet caches, shared by all vendors.
DEFAULT_CACHE_DIR = ".cache"


class DataVendor(ABC):
    """Abstract base class all data vendors implement.

    A vendor knows how to fetch raw market data for a symbol and return it
    as a pandas DataFrame indexed by ``datetime``. Concrete vendors may
    additionally expose vendor-specific methods (e.g. tick-level trades),
    but the methods below form the common contract.

    Args:
        cache_dir: Directory for parquet caches of fetched data.
    """

    #: Short identifier used in the vendor registry (e.g. ``"binance"``).
    name: str

    def __init__(self, cache_dir: str | Path = DEFAULT_CACHE_DIR) -> None:
        self.cache_dir = Path(cache_dir)

    @abstractmethod
    def fetch_ohlc(
        self,
        symbol: str,
        start_date: str | datetime,
        end_date: str | datetime,
        time_interval: str = "1h",
    ) -> pd.DataFrame:
        """Fetch OHLC(V) bars for ``symbol`` between two dates (inclusive).

        Args:
            symbol: Vendor-specific symbol (e.g. ``"BTCUSDT"``, ``"AAPL"``).
            start_date: Start date (inclusive), ``YYYY-MM-DD`` or datetime.
            end_date: End date (inclusive), ``YYYY-MM-DD`` or datetime.
            time_interval: Pandas offset alias (e.g. ``"1h"``, ``"5min"``, ``"1D"``).

        Returns:
            DataFrame indexed by ``datetime`` with columns
            ``open, high, low, close`` (and ``volume`` if available).
        """

    def fetch_ohlc_many(
        self,
        symbols: list[str],
        start_date: str | datetime,
        end_date: str | datetime,
        time_interval: str = "1D",
    ) -> dict[str, pd.DataFrame]:
        """Fetch OHLCV bars for multiple symbols with a progress bar.

        Symbols that fail are skipped with a warning.

        Returns:
            Mapping of symbol to OHLCV DataFrame.
        """
        out: dict[str, pd.DataFrame] = {}
        for symbol in tqdm(symbols, desc=f"Fetching OHLC ({self.name})"):
            try:
                out[symbol] = self.fetch_ohlc(
                    symbol, start_date, end_date, time_interval
                )
            except Exception as e:  # noqa: BLE001 - skip bad symbols, keep going
                logger.warning("%s: %s", symbol, e)
        return out

    def _cached(
        self,
        cache_path: Path,
        fetch: Callable[[], pd.DataFrame],
        index: str | None = None,
    ) -> pd.DataFrame:
        """Return ``cache_path`` as a DataFrame, calling ``fetch`` on a miss.

        On a cache miss the result of ``fetch()`` is written to
        ``cache_path`` as parquet before being returned.

        Parquet I/O goes through DuckDB rather than pandas/pyarrow: pyarrow's
        CPU thread pool can intermittently deadlock the interpreter at exit
        (its teardown races Python finalization; observed on pyarrow 23-25).

        Args:
            cache_path: Parquet file backing this result.
            fetch: Zero-arg callable producing the DataFrame on a miss.
            index: Column to restore as the DataFrame index (DuckDB does not
                preserve pandas indexes, so it is stored as a plain column).
        """
        if cache_path.exists():
            df = duckdb.read_parquet(str(cache_path)).df()
            return df.set_index(index) if index else df

        df = fetch()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        out = df.reset_index() if index else df
        duckdb.from_df(out).write_parquet(str(cache_path))
        logger.info("Cached %s rows to %s", len(df), cache_path)
        return df


def trades_to_ohlc(trades: pd.DataFrame, time_interval: str) -> pd.DataFrame:
    """Aggregate tick trades into OHLCV bars.

    Expects ``datetime``, ``price`` and ``qty`` columns.
    """
    trades = trades.set_index("datetime").sort_index()
    ohlc = trades["price"].resample(time_interval).ohlc()
    ohlc["volume"] = trades["qty"].resample(time_interval).sum()
    return ohlc.dropna(subset=["open"])


def _no_data_error(
    symbol: str, start_date: str | datetime, end_date: str | datetime
) -> ValueError:
    """Build the standard 'no data' error for a symbol/range."""
    return ValueError(
        f"No data available for {symbol} in range {start_date} to {end_date}"
    )


def _normalize_range(
    start_date: str | datetime, end_date: str | datetime
) -> tuple[datetime, datetime]:
    """Parse and validate an inclusive date range."""
    start = _normalize_date(start_date)
    end = _normalize_date(end_date)
    if start > end:
        raise ValueError("start_date must be before or equal to end_date")
    return start, end


def _normalize_date(date: str | datetime) -> datetime:
    """Parse a ``YYYY-MM-DD`` string into a datetime (pass through datetimes)."""
    if isinstance(date, datetime):
        return date
    return datetime.strptime(date, "%Y-%m-%d")
