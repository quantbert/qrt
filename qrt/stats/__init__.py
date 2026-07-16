"""Statistical analytics for return streams: performance, risk, and benchmark-relative metrics.

Use :func:`returns` to bind a return stream (and optional benchmark) for
chained stats and plotting, e.g. ``q.stats.returns(returns, benchmark=spy).alpha()``.
Plain functions (e.g. ``q.stats.performance(returns)``) are stateless and take
the series directly. See :mod:`qrt.plot` for rendering return streams.
"""

from qrt.stats.core import (
    Returns,
    ReturnType,
    alpha,
    benchmark_stats,
    beta,
    infer_periods_per_year,
    monthly_returns,
    performance,
    returns,
    rolling_alpha,
    rolling_beta,
    rolling_sharpe,
    rolling_volatility,
)

__all__ = [
    "Returns",
    "ReturnType",
    "alpha",
    "benchmark_stats",
    "beta",
    "infer_periods_per_year",
    "monthly_returns",
    "performance",
    "returns",
    "rolling_alpha",
    "rolling_beta",
    "rolling_sharpe",
    "rolling_volatility",
]
