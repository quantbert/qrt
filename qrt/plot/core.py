"""Plotly plotting primitives for financial time series.

Statistical computations (performance, alpha/beta, rolling diagnostics, ...)
live in :mod:`qrt.stats`; this module focuses on rendering.
"""

from __future__ import annotations

from collections.abc import Iterable
from fnmatch import fnmatch
from typing import TYPE_CHECKING

import pandas as pd

from qrt.stats import ReturnType

if TYPE_CHECKING:
    from plotly.graph_objects import Figure


def _as_frame(data: pd.Series | pd.DataFrame, columns: str | Iterable[str] | None) -> pd.DataFrame:
    """Return selected numeric columns, expanding shell-style column patterns."""
    frame = data.to_frame(name=data.name or "value") if isinstance(data, pd.Series) else data.copy()
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("data must be a pandas Series or DataFrame")

    requested = list(frame.columns) if columns is None else [columns] if isinstance(columns, str) else list(columns)
    selected: list[str] = []
    available = [str(column) for column in frame.columns]
    for pattern in requested:
        matches = [column for column in available if fnmatch(column, pattern)]
        if not matches:
            raise KeyError(f"No columns match {pattern!r}. Available columns: {available}")
        selected.extend(column for column in matches if column not in selected)

    result = frame.loc[:, selected]
    non_numeric = result.select_dtypes(exclude="number").columns.tolist()
    if non_numeric:
        raise TypeError(f"Plot columns must be numeric; got {non_numeric}")
    return result


def monthly_heatmap(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    title: str = "Monthly returns",
    height: int | None = None,
) -> Figure:
    """Create an interactive Plotly calendar-month return heatmap.

    Args:
        returns: Periodic return series with a ``DatetimeIndex``.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        title: Figure title.
        height: Figure height in pixels. Defaults to a size based on the
            number of years.

    Returns:
        A Plotly ``Figure``.
    """
    from qrt.plot.interactive import monthly_heatmap as _monthly_heatmap

    return _monthly_heatmap(returns, return_type=return_type, title=title, height=height)


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
    from qrt.plot.interactive import line

    return line(data, columns, title=title, yaxis_title=ylabel, height=height)


def equity(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    title: str = "Equity curve",
    label: str | None = None,
    height: int = 450,
) -> Figure:
    """Create an interactive compounded equity curve from periodic returns.

    Args:
        returns: Periodic return series.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        title: Figure title.
        label: Series name for the equity curve. Defaults to ``returns.name``.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    from qrt.plot.interactive import equity as _equity

    return _equity(returns, return_type=return_type, title=title, label=label, height=height)


def drawdown(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    title: str = "Drawdown",
    height: int = 320,
) -> Figure:
    """Create an interactive underwater chart from periodic returns.

    Args:
        returns: Periodic return series.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        title: Figure title.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    from qrt.plot.interactive import drawdown as _drawdown

    return _drawdown(returns, return_type=return_type, title=title, height=height)


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
    from qrt.plot.interactive import performance as _performance_plot

    return _performance_plot(
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


def show(
    figure: object,
    name: str | None = None,
    *,
    save_to: str | None = None,
    formats: Iterable[str] = ("png",),
    width: int = 1400,
    height: int = 800,
    scale: int = 2,
) -> None:
    """Display a Plotly figure, optionally saving it to `save_to` as PNG (default) and/or self-contained HTML.

    Args:
        figure: Plotly figure to display (and optionally save).
        name: File stem used when saving. Required if ``save_to`` is given.
        save_to: Directory to save the figure into. If ``None``, the figure
            is only displayed.
        formats: Output formats to save, any of ``"png"`` and/or ``"html"``.
        width: PNG width in pixels.
        height: PNG height in pixels.
        scale: PNG scale factor (for higher-resolution exports).
    """
    from qrt.plot.interactive import show as _show

    _show(
        figure,
        name,
        save_to=save_to,
        formats=formats,
        width=width,
        height=height,
        scale=scale,
    )