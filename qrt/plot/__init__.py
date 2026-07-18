"""Opinionated static and interactive plots for quantitative research.

The first helpers focus on return streams: quick column charts, equity curves,
drawdowns, and compact performance tearsheets. The Plotly implementations live
in :mod:`qrt.plot.interactive` and are re-exported here; this module only adds
the ergonomic aliases :func:`col`, :func:`plot`, and :func:`tearsheet`.
Return-stream statistics (performance, alpha/beta, rolling diagnostics, ...)
live in :mod:`qrt.stats`.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

import pandas as pd

from qrt.plot import interactive
from qrt.plot.interactive import (
    cumulative_returns,
    daily_returns,
    drawdown,
    eoy_returns,
    equity,
    mae_mfe,
    metrics_table,
    monthly_distribution,
    monthly_heatmap,
    montecarlo,
    montecarlo_distribution,
    noise_test,
    report,
    return_quantiles,
    rolling_beta,
    rolling_sharpe,
    rolling_sortino,
    rolling_volatility,
    show,
    trade_distribution,
    trades,
    variance_test,
    worst_drawdowns,
)
from qrt.stats import ReturnType

if TYPE_CHECKING:
    from plotly.graph_objects import Figure


def col(
    data: pd.Series | pd.DataFrame,
    columns: str | Iterable[str] | None = None,
    *,
    title: str | None = None,
    ylabel: str | None = None,
    height: int = 450,
) -> Figure:
    """Create an interactive Plotly line chart from selected numeric columns.

    Args:
        data: Series or DataFrame to plot.
        columns: Column name(s) or shell-style pattern(s) (e.g. ``"*_ret"``)
            to select. Defaults to all columns.
        title: Figure title. Defaults to the column name (single column) or
            a generic title (multiple columns).
        ylabel: Y-axis label.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    return interactive.line(data, columns, title=title, yaxis_title=ylabel, height=height)


def plot(
    returns: pd.Series,
    *,
    benchmark: pd.Series | None = None,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
    title: str | None = None,
    height: int = 700,
) -> Figure:
    """Create an interactive Plotly equity-and-drawdown performance report.

    Alias for :func:`qrt.plot.interactive.performance`.

    Args:
        returns: Strategy periodic return series.
        benchmark: Optional benchmark periodic return series, aligned to
            ``returns`` on shared dates.
        return_type: Whether ``returns``/``benchmark`` are ``"simple"`` or
            ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.
        title: Figure title. Defaults to ``returns.name``.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    return interactive.performance(
        returns,
        benchmark=benchmark,
        return_type=return_type,
        periods_per_year=periods_per_year,
        title=title,
        height=height,
    )


def tearsheet(returns: pd.Series, **kwargs: object) -> Figure:
    """Alias for the interactive :func:`plot` performance report.

    Args:
        returns: Strategy periodic return series.
        **kwargs (Any): Forwarded to :func:`plot` (e.g. ``benchmark``, ``title``).

    Returns:
        A Plotly ``Figure``.
    """
    return plot(returns, **kwargs)  # type: ignore[arg-type]


__all__ = [
    "col",
    "cumulative_returns",
    "daily_returns",
    "drawdown",
    "eoy_returns",
    "equity",
    "interactive",
    "mae_mfe",
    "metrics_table",
    "monthly_distribution",
    "monthly_heatmap",
    "montecarlo",
    "montecarlo_distribution",
    "noise_test",
    "plot",
    "report",
    "return_quantiles",
    "rolling_beta",
    "rolling_sharpe",
    "rolling_sortino",
    "rolling_volatility",
    "show",
    "tearsheet",
    "trade_distribution",
    "trades",
    "variance_test",
    "worst_drawdowns",
]
