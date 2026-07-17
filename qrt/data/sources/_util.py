"""Shared internals for data source modules -- not part of the public API."""

import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd
from tqdm import tqdm

from qrt.utils import cache_dir

logger = logging.getLogger(__name__)

#: Default directory for parquet caches, shared by all sources (OS-standard
#: user cache dir, e.g. ~/.cache/qrt/data on Linux -- doesn't depend on cwd).
DEFAULT_CACHE_DIR = cache_dir("data")


def cached(
    cache_path: Path,
    fetch: Callable[[], pd.DataFrame],
    index: str | None = None,
) -> pd.DataFrame:
    """Return ``cache_path`` as a DataFrame, calling ``fetch`` on a miss.

    On a cache miss the result of ``fetch()`` is written to ``cache_path``
    as parquet before being returned.

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


def read_many(
    symbols: list[str],
    read_one: Callable[[str], pd.DataFrame],
    desc: str,
) -> dict[str, pd.DataFrame]:
    """Read multiple symbols via ``read_one``, skipping failures with a warning.

    Args:
        symbols: Symbols to read.
        read_one: Callable taking a single symbol and returning its DataFrame.
        desc: Progress bar description.

    Returns:
        Mapping of symbol to DataFrame (failed symbols are omitted).
    """
    out: dict[str, pd.DataFrame] = {}
    for symbol in tqdm(symbols, desc=desc):
        try:
            out[symbol] = read_one(symbol)
        except Exception as e:  # noqa: BLE001 - skip bad symbols, keep going
            logger.warning("%s: %s", symbol, e)
    return out


def trades_to_ohlc(trades: pd.DataFrame, time_interval: str) -> pd.DataFrame:
    """Aggregate tick trades into OHLCV bars.

    Expects ``datetime``, ``price`` and ``qty`` columns.
    """
    trades = trades.set_index("datetime").sort_index()
    ohlc = trades["price"].resample(time_interval).ohlc()
    ohlc["volume"] = trades["qty"].resample(time_interval).sum()
    return ohlc.dropna(subset=["open"])


def no_data_error(
    symbol: str, start_date: str | datetime, end_date: str | datetime
) -> ValueError:
    """Build the standard 'no data' error for a symbol/range."""
    return ValueError(
        f"No data available for {symbol} in range {start_date} to {end_date}"
    )


def normalize_range(
    start_date: str | datetime, end_date: str | datetime
) -> tuple[datetime, datetime]:
    """Parse and validate an inclusive date range."""
    start = normalize_date(start_date)
    end = normalize_date(end_date)
    if start > end:
        raise ValueError("start_date must be before or equal to end_date")
    return start, end


def normalize_date(date: str | datetime) -> datetime:
    """Parse a ``YYYY-MM-DD`` string into a datetime (pass through datetimes)."""
    if isinstance(date, datetime):
        return date
    return datetime.strptime(date, "%Y-%m-%d")
