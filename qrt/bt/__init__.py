"""Event-driven backtesting of model signals against price data.

    q.bt.run(signal, prices)

Add new concerns (transaction cost models, trade logs, ...) as additional
modules in this package as they land, same convention as ``q.feat``/``q.data``.
"""

__all__ = ["run"]


def run(signal, prices):
    """Run a backtest. Placeholder."""
    raise NotImplementedError
