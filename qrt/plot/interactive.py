"""Interactive Plotly charts for quantitative research return streams."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from qrt.plot.core import (
    ReturnType,
    _aligned_returns,
    _as_frame,
    _periods_per_year,
    _simple_returns,
    monthly_returns,
    performance as performance_stats,
)

if TYPE_CHECKING:
    from plotly.graph_objects import Figure

_QUANT_COLORS = ("#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2", "#B279A2")


def _base_layout(
    figure: Figure, *, title: str | None = None, height: int | None = None, time_axis: bool = True
) -> Figure:
    """Apply the shared interactive chart affordances and styling."""
    figure.update_layout(
        template="plotly_white",
        title=title,
        hovermode="x unified",
        height=height,
        margin={"l": 60, "r": 30, "t": 90, "b": 50},
        legend={"orientation": "h", "y": 1.02, "x": 0, "xanchor": "left"},
    )
    figure.update_xaxes(showgrid=False)
    if time_axis:
        figure.update_xaxes(
            rangeselector={
                "buttons": [
                    {"count": 1, "label": "1m", "step": "month", "stepmode": "backward"},
                    {"count": 6, "label": "6m", "step": "month", "stepmode": "backward"},
                    {"count": 1, "label": "YTD", "step": "year", "stepmode": "todate"},
                    {"count": 1, "label": "1y", "step": "year", "stepmode": "backward"},
                    {"step": "all", "label": "All"},
                ]
            },
            rangeslider_visible=False,
        )
    figure.update_yaxes(showgrid=True, gridcolor="#E5E7EB", zeroline=False)
    return figure


def _set_date_range(figure: Figure, index: pd.Index, **kwargs: object) -> None:
    """Pin the x-axis range to the actual data span for reliable rendering."""
    if isinstance(index, pd.DatetimeIndex) and len(index):
        date_range = [index.min().isoformat(), index.max().isoformat()]
        figure.update_xaxes(range=date_range, **kwargs)


def line(
    data: pd.Series | pd.DataFrame,
    columns: str | Iterable[str] | None = None,
    *,
    title: str | None = None,
    yaxis_title: str | None = None,
    height: int = 450,
) -> Figure:
    """Create an interactive line chart from selected Series or DataFrame columns.

    Column selection supports the same shell-style patterns as :func:`qrt.plot.col`.
    The returned Plotly figure supports hover, zoom, pan, and range selection.
    """
    frame = _as_frame(data, columns)
    figure = go.Figure()
    for index, column in enumerate(frame.columns):
        figure.add_scatter(
            x=frame.index,
            y=frame[column],
            mode="lines",
            name=str(column),
            line={"color": _QUANT_COLORS[index % len(_QUANT_COLORS)], "width": 1.8},
        )
    chart_title = title or (str(frame.columns[0]) if len(frame.columns) == 1 else "Quantitative research series")
    _base_layout(figure, title=chart_title, height=height)
    _set_date_range(figure, frame.index)
    figure.update_yaxes(title_text=yaxis_title)
    return figure


def equity(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    title: str = "Equity curve",
    label: str | None = None,
    height: int = 450,
) -> Figure:
    """Create an interactive compounded equity curve from periodic returns."""
    series = _simple_returns(returns, return_type)
    curve = (1.0 + series).cumprod().rename(label or series.name or "Equity")
    figure = line(curve, title=title, yaxis_title="Growth of $1", height=height)
    figure.add_hline(y=1.0, line={"color": "#6B7280", "width": 1, "dash": "dash"})
    return figure


def drawdown(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    title: str = "Drawdown",
    height: int = 320,
) -> Figure:
    """Create an interactive underwater chart from periodic returns."""
    series = _simple_returns(returns, return_type)
    underwater = (1.0 + series).cumprod().div((1.0 + series).cumprod().cummax()).sub(1.0)
    figure = go.Figure(
        go.Scatter(
            x=underwater.index,
            y=underwater,
            mode="lines",
            name="Drawdown",
            line={"color": _QUANT_COLORS[3], "width": 1.5},
            fill="tozeroy",
            fillcolor="rgba(228, 87, 86, 0.25)",
        )
    )
    _base_layout(figure, title=title, height=height)
    _set_date_range(figure, underwater.index)
    figure.update_yaxes(title_text="Drawdown", tickformat=".0%")
    return figure


def performance(
    returns: pd.Series,
    *,
    benchmark: pd.Series | None = None,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
    title: str | None = None,
    height: int = 700,
) -> Figure:
    """Create an interactive equity, drawdown, and headline-statistics report.

    The figure has linked time axes, unified hover, zooming, and date-range
    buttons. If supplied, the benchmark is aligned to the strategy's shared
    observations before plotting.
    """
    reference: pd.Series | None = None
    if benchmark is not None:
        strategy, reference = _aligned_returns(returns, benchmark, return_type)
    else:
        strategy = _simple_returns(returns, return_type, "Strategy")

    strategy_curve = (1.0 + strategy).cumprod()
    strategy_drawdown = strategy_curve.div(strategy_curve.cummax()).sub(1.0)
    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=(0.72, 0.28),
        vertical_spacing=0.06,
        subplot_titles=("Equity curve", "Drawdown"),
    )
    figure.add_scatter(
        x=strategy_curve.index,
        y=strategy_curve,
        mode="lines",
        name=strategy.name or "Strategy",
        line={"color": _QUANT_COLORS[0], "width": 2},
        row=1,
        col=1,
    )
    if reference is not None:
        benchmark_curve = (1.0 + reference).cumprod()
        figure.add_scatter(
            x=benchmark_curve.index,
            y=benchmark_curve,
            mode="lines",
            name=reference.name or "Benchmark",
            line={"color": _QUANT_COLORS[1], "width": 2},
            row=1,
            col=1,
        )
    figure.add_hline(y=1.0, line={"color": "#6B7280", "width": 1, "dash": "dash"}, row=1, col=1)
    figure.add_scatter(
        x=strategy_drawdown.index,
        y=strategy_drawdown,
        mode="lines",
        name="Drawdown",
        line={"color": _QUANT_COLORS[3], "width": 1.5},
        fill="tozeroy",
        fillcolor="rgba(228, 87, 86, 0.25)",
        row=2,
        col=1,
    )

    annualization = _periods_per_year(periods_per_year, strategy.index)
    stats = performance_stats(strategy, periods_per_year=annualization)
    stat_text = " &nbsp; ".join(
        [
            f"<b>CAGR</b> {stats['CAGR']:.2%}",
            f"<b>Volatility</b> {stats['Volatility']:.2%}",
            f"<b>Sharpe</b> {stats['Sharpe']:.2f}",
            f"<b>Max DD</b> {stats['Max Drawdown']:.2%}",
        ]
    )
    _base_layout(figure, title=title or strategy.name or "Performance report", height=height)
    figure.update_layout(annotations=[*figure.layout.annotations, {"text": stat_text, "showarrow": False, "x": 0, "xanchor": "left", "y": 1.12, "yref": "paper"}])
    _set_date_range(figure, strategy_curve.index, row=1, col=1)
    _set_date_range(figure, strategy_curve.index, row=2, col=1)
    figure.update_yaxes(title_text="Growth of $1", row=1, col=1)
    figure.update_yaxes(title_text="Drawdown", tickformat=".0%", row=2, col=1)
    return figure


def monthly_heatmap(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    title: str = "Monthly returns",
    height: int | None = None,
) -> Figure:
    """Create an interactive, annotated calendar-month return heatmap."""
    table = monthly_returns(returns, return_type=return_type)
    values = table.to_numpy(dtype=float)
    finite_values = values[np.isfinite(values)]
    limit = max(abs(finite_values.min()), abs(finite_values.max())) if len(finite_values) else 0.01
    text = np.where(np.isfinite(values), np.char.mod("%.1f%%", values * 100), "")
    figure = go.Figure(
        go.Heatmap(
            z=values,
            x=[pd.Timestamp(2000, month, 1).strftime("%b") for month in table.columns],
            y=table.index.astype(str),
            text=text,
            texttemplate="%{text}",
            textfont={"size": 11},
            colorscale="RdYlGn",
            zmid=0,
            zmin=-limit,
            zmax=limit,
            colorbar={"title": "Return", "tickformat": ".0%"},
            hovertemplate="Year %{y}<br>Month %{x}<br>Return %{z:.2%}<extra></extra>",
        )
    )
    _base_layout(figure, title=title, height=height or max(320, 80 * len(table) + 170), time_axis=False)
    figure.update_layout(hovermode="closest")
    figure.update_xaxes(side="top")
    figure.update_yaxes(autorange="reversed", showgrid=False, title_text="")
    return figure


__all__ = ["drawdown", "equity", "line", "monthly_heatmap", "performance"]
