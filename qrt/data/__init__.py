"""Data access: loading/saving local files, downloading from market data
sources, and prepackaged sample datasets -- everything data-related lives
under this subpackage.

    import qrt as q

    df = q.data.load("ohlc.parquet")
    q.data.save(df, "ohlc.parquet")

    ohlc = q.data.sources.yfinance.read("AAPL", "2024-01-01", "2025-01-01", "1d")

    spy = q.data.datasets.load("spy")  # prepackaged, works offline
"""

from qrt.data import datasets, sources
from qrt.data.local import load, load_ohlc_timeseries_range, save

__all__ = ["datasets", "load", "load_ohlc_timeseries_range", "save", "sources"]
