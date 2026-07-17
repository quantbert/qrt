"""Local file loading and saving (parquet, csv, ...) plus raw trade
aggregation from cached files.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)


def load(path: str | Path, index: str | None = None) -> pd.DataFrame:
    """Load a local data file into a DataFrame.

    Dispatches on the file suffix: ``.parquet`` is read via DuckDB (see
    :func:`~qrt.data.sources._util.cached` for why), ``.csv`` via pandas.

    Args:
        path: File to load.
        index: Column to set as the index, if any.

    Returns:
        The loaded DataFrame.

    Raises:
        ValueError: If the file suffix isn't ``.parquet`` or ``.csv``.
    """
    path = Path(path)
    if path.suffix == ".parquet":
        df = duckdb.read_parquet(str(path)).df()
    elif path.suffix == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")
    return df.set_index(index) if index else df


def save(df: pd.DataFrame, path: str | Path, index: bool = False) -> None:
    """Save a DataFrame to a local file.

    Dispatches on the file suffix: ``.parquet`` is written via DuckDB,
    ``.csv`` via pandas.

    Args:
        df: DataFrame to save.
        path: Destination file. Parent directories are created if needed.
        index: Whether to keep the DataFrame index as a leading column.

    Raises:
        ValueError: If the file suffix isn't ``.parquet`` or ``.csv``.
    """
    path = Path(path)
    if path.suffix not in (".parquet", ".csv"):
        raise ValueError(f"Unsupported file type: {path.suffix}")

    path.parent.mkdir(parents=True, exist_ok=True)
    out = df.reset_index() if index else df
    if path.suffix == ".parquet":
        duckdb.from_df(out).write_parquet(str(path))
    else:
        out.to_csv(path, index=False)


def load_ohlc_timeseries_range(
    sym: str,
    time_interval: str,
    start_date: datetime,
    end_date: datetime,
    data_path: str | Path = "./cache",
) -> pd.DataFrame:
    """Load daily trade CSV files and aggregate them into OHLC bars.

    Expects daily files named like ``{sym}-trades-YYYY-MM-DD.csv``, e.g.
    ``BTCUSDT-trades-2025-09-22.csv``, containing at least a ``datetime``
    and a ``price`` column. A ``qty`` column, if present, is summed into
    a ``volume`` column.

    Args:
        sym: Symbol prefix (e.g. ``"BTCUSDT"``).
        time_interval: Pandas offset alias (e.g. ``"1h"``, ``"5min"``).
        start_date: Start datetime (inclusive).
        end_date: End datetime (inclusive).
        data_path: Directory containing the cached trade CSV files.

    Returns:
        DataFrame indexed by ``datetime`` with columns
        ``open, high, low, close`` (and ``volume`` if available).
    """
    if start_date > end_date:
        raise ValueError("start_date must be before or equal to end_date")

    data_path = Path(data_path)
    frames = []
    for i in range((end_date - start_date).days + 1):
        day = start_date + timedelta(days=i)
        file_path = data_path / f"{sym}-trades-{day:%Y-%m-%d}.csv"
        if not file_path.exists():
            logger.warning("Missing file: %s", file_path.name)
            continue

        trades = pd.read_csv(file_path)
        if "datetime" not in trades.columns:
            raise ValueError(f"Column 'datetime' not found in {file_path.name}")
        trades["datetime"] = pd.to_datetime(trades["datetime"])
        frames.append(trades)

    if not frames:
        raise ValueError(
            f"No trade data found for {sym} in range {start_date} to {end_date}"
        )

    trades = pd.concat(frames).set_index("datetime").sort_index()
    ohlc = trades["price"].resample(time_interval).ohlc()
    if "qty" in trades.columns:
        ohlc["volume"] = trades["qty"].resample(time_interval).sum()
    return ohlc.dropna(subset=["open"])
