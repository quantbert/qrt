"""Prepackaged sample datasets (daily OHLCV) shipped with qrt for offline
use -- handy for tests, demos, and tutorials without hitting yfinance every
time you just need some SPY or AAPL data on hand.

    import qrt as q

    spy = q.data.datasets.load("spy")
    aapl = q.data.datasets.load("aapl")

The bundled parquet files are refreshed via :func:`refresh` (see
``tools/update_datasets.py``, wired into ``make datasets`` /
``make publish``) so released versions of qrt always ship reasonably
current data -- but they are not guaranteed to be fully up to date for a
given install. Fetch live data via :mod:`qrt.data.sources` if you need the
latest bar.
"""

from datetime import date, datetime
from pathlib import Path

import pandas as pd

from qrt.data.local import load as _load_file
from qrt.data.local import save as _save_file

#: dataset name -> yfinance ticker symbol.
_SYMBOLS: dict[str, str] = {
    "aapl": "AAPL",
    "spy": "SPY",
    "btcusd": "BTC-USD",
}

#: Datasets fetch this far back; each symbol's actual first row depends on
#: when Yahoo's history for it begins (e.g. BTC-USD only goes back to 2014).
START_DATE = "2000-01-01"

_DIR = Path(__file__).parent

AVAILABLE = tuple(sorted(_SYMBOLS))


def load(name: str) -> pd.DataFrame:
    """Load a bundled sample dataset (offline, no network required).

    Args:
        name: One of :data:`AVAILABLE` (``"aapl"``, ``"btcusd"``, ``"spy"``).

    Returns:
        Daily OHLCV DataFrame indexed by ``datetime``.

    Raises:
        KeyError: If ``name`` isn't a bundled dataset.
    """
    if name not in _SYMBOLS:
        raise KeyError(f"Unknown dataset {name!r}. Available: {list(AVAILABLE)}")
    return _load_file(_DIR / f"{name}.parquet", index="datetime")


def refresh(names: list[str] | None = None, end_date: str | date | None = None) -> None:
    """Re-download bundled datasets from Yahoo Finance and overwrite their parquet files.

    Args:
        names: Dataset names to refresh (default: all of :data:`AVAILABLE`).
        end_date: Last date to fetch, ``YYYY-MM-DD`` (default: today).
    """
    # Imported lazily: qrt.data.sources pulls in yfinance/requests/duckdb,
    # unnecessary weight for the common case of just loading bundled data.
    from qrt.data.sources import yfinance as _yfinance

    names = names or list(AVAILABLE)
    end = end_date or datetime.today().strftime("%Y-%m-%d")

    for name in names:
        symbol = _SYMBOLS[name]
        df = _yfinance.read(symbol, START_DATE, end, "1D")
        _save_file(df, _DIR / f"{name}.parquet", index=True)
        print(f"Updated {name}.parquet: {len(df)} rows ({symbol}, {df.index[0]:%Y-%m-%d} to {df.index[-1]:%Y-%m-%d})")
