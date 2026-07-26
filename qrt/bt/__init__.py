"""Backtest execution and reporting.

``q.bt.report(...)`` turns a LEAN result JSON into a native qrt report without
starting LEAN's standalone Report Creator or replaying its orders.
"""

from qrt.bt import lean as lean
from qrt.bt._report import BacktestReport, report


__all__ = ["BacktestReport", "lean", "report", "run"]


def run(signal, prices):
    """Run a backtest. Placeholder."""
    raise NotImplementedError
