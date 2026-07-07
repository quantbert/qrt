"""Data loading from local file caches."""

import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


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
