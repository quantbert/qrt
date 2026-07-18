"""Prepackaged sample datasets shipped with qrt for offline use -- handy
for tests, demos, and tutorials without hitting yfinance every time you
just need some SPY or AAPL data on hand.

Two kinds of datasets are bundled:

* Daily OHLCV price history (``"aapl"``, ``"spy"``, ``"btcusd"``),
  indexed by ``datetime``.
* Demo strategy **trade logs** in qrt's canonical trades format
  (``"spy_ema_cross"``, ``"spy_rsi2"``, ``"spy_random"``,
  ``"spy_breakout"``) -- one row per round-trip trade with entry/exit
  time, price and reason, direction (``1`` = long, ``-1`` = short),
  direction-adjusted decimal ``return``, MAE/MFE, and per-strategy
  entry-time feature snapshots. Generated deterministically from the
  bundled SPY data by ``tools/gen_demo_strategies.py``.

    import qrt as q

    spy = q.data.datasets.load("spy")
    trades = q.data.datasets.load("spy_rsi2")

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

#: Demo strategy trade-log datasets (canonical trades format), generated
#: from the bundled SPY data by ``tools/gen_demo_strategies.py``.
TRADE_LOGS = ("spy_breakout", "spy_ema_cross", "spy_random", "spy_rsi2")

_DIR = Path(__file__).parent

AVAILABLE = tuple(sorted((*_SYMBOLS, *TRADE_LOGS)))


def load(name: str) -> pd.DataFrame:
    """Load a bundled sample dataset (offline, no network required).

    Args:
        name: One of :data:`AVAILABLE` -- a daily OHLCV dataset
            (``"aapl"``, ``"btcusd"``, ``"spy"``) or a demo strategy
            trade log (see :data:`TRADE_LOGS`).

    Returns:
        For OHLCV datasets, a daily OHLCV DataFrame indexed by
        ``datetime``. For trade logs, a trades-format DataFrame (one row
        per trade, plain integer index).

    Raises:
        KeyError: If ``name`` isn't a bundled dataset.
    """
    if name in TRADE_LOGS:
        return _load_file(_DIR / f"{name}.parquet")
    if name not in _SYMBOLS:
        raise KeyError(f"Unknown dataset {name!r}. Available: {list(AVAILABLE)}")
    return _load_file(_DIR / f"{name}.parquet", index="datetime")


def refresh(names: list[str] | None = None, end_date: str | date | None = None) -> None:
    """Re-download bundled OHLCV datasets from Yahoo Finance and overwrite their parquet files.

    Trade-log datasets (:data:`TRADE_LOGS`) are not refreshed here -- they
    are regenerated from the bundled SPY data by
    ``tools/gen_demo_strategies.py`` (run it after refreshing).

    Args:
        names: OHLCV dataset names to refresh (default: all of them).
        end_date: Last date to fetch, ``YYYY-MM-DD`` (default: today).

    Raises:
        ValueError: If ``names`` contains a non-OHLCV dataset name.
    """
    # Imported lazily: qrt.data.sources pulls in yfinance/requests/duckdb,
    # unnecessary weight for the common case of just loading bundled data.
    from qrt.data.sources import yfinance as _yfinance

    names = names or list(sorted(_SYMBOLS))
    unknown = [n for n in names if n not in _SYMBOLS]
    if unknown:
        raise ValueError(
            f"Not refreshable OHLCV dataset(s): {unknown}. "
            f"Available: {sorted(_SYMBOLS)}"
        )
    end = end_date or datetime.today().strftime("%Y-%m-%d")

    for name in names:
        symbol = _SYMBOLS[name]
        df = _yfinance.read(symbol, START_DATE, end, "1D")
        _save_file(df, _DIR / f"{name}.parquet", index=True)
        print(f"Updated {name}.parquet: {len(df)} rows ({symbol}, {df.index[0]:%Y-%m-%d} to {df.index[-1]:%Y-%m-%d})")
