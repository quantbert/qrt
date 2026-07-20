"""Data sources: network vendors, databases, and other backends -- each
exposed as its own explicit submodule.

    import qrt as q

    ohlc = q.data.sources.yfinance.read("AAPL", "2024-01-01", "2025-01-01", "1d")
    ohlc = q.data.sources.binance.read("BTCUSDT", "2025-01-01", "2025-01-07", "1h")

    with q.data.sources.duckdb.connect(path="prod.duckdb") as db:
        db.write(ohlc, table="ohlc")

To add a new source, create ``qrt/data/sources/<name>.py`` with whatever
functions/classes make sense for that backend (no shared base class
required), then register it below.
"""

from qrt.data.sources import binance, duckdb, yfinance

__all__ = [
    "binance",
    "duckdb",
    "yfinance",
]
