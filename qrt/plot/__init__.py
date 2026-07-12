"""Opinionated Matplotlib plots for quantitative research.

The first helpers focus on return streams: quick column charts, equity curves,
drawdowns, and a compact performance tearsheet.
"""

from qrt.plot.core import col, drawdown, equity, qplot, tearsheet

__all__ = ["col", "drawdown", "equity", "qplot", "tearsheet"]
