"""Interactive Plotly charts for quantitative research return streams."""

from __future__ import annotations

from collections.abc import Iterable
from fnmatch import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from qrt.stats.core import (
    CovarianceType,
    ReturnType,
    _aligned_returns,
    _periods_per_year,
    _simple_returns,
    aggregate_returns,
    distribution as distribution_stats,
    drawdown_details,
    factor_contributions as factor_contributions_stats,
    factor_regression as factor_regression_stats,
    metrics as metrics_stats,
    monthly_returns,
    performance as performance_stats,
    rolling_beta as rolling_beta_stats,
    rolling_factor_regression as rolling_factor_regression_stats,
    rolling_sharpe as rolling_sharpe_stats,
    rolling_sortino as rolling_sortino_stats,
    rolling_volatility as rolling_volatility_stats,
    to_drawdown_series as to_drawdown_series_,
)

if TYPE_CHECKING:
    from plotly.graph_objects import Figure

_QUANT_COLORS = ("#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2", "#B279A2")


def _monthly_heatmap_row_height(n_years: int) -> int:
    """Compact pixel height for a monthly-returns heatmap's plotting area, scaled by year count."""
    return max(280, 28 * n_years + 110)


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


def _base_layout(
    figure: Figure,
    *,
    title: str | None = None,
    subtitle: str | None = None,
    height: int | None = None,
    time_axis: bool = True,
) -> Figure:
    """Apply the shared interactive chart affordances and styling."""
    figure.update_layout(
        template="plotly_white",
        title={"text": title, "subtitle": {"text": subtitle}} if subtitle else title,
        hovermode="x unified",
        height=height,
        margin={"l": 60, "r": 30, "t": 115 if subtitle else 90, "b": 50},
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
            # Since _set_date_range pins the range to the exact data span, the "instant" (default)
            # tick label mode would drop the first/last year label whenever it falls outside that
            # pinned range (e.g. data starting mid-year). "period" instead centers each label within
            # its (possibly partial) visible span, so edge years always get a label.
            ticklabelmode="period",
        )
    figure.update_yaxes(showgrid=True, gridcolor="#E5E7EB", zeroline=False)
    return figure


def _set_date_range(figure: Figure, index: pd.Index, **kwargs: object) -> None:
    """Pin the x-axis range to the actual data span for reliable rendering."""
    if isinstance(index, pd.DatetimeIndex) and len(index):
        date_range = [index.min().isoformat(), index.max().isoformat()]
        figure.update_xaxes(range=date_range, **kwargs)


def _log_percent_ticks(*curves: pd.Series) -> tuple[list[float], list[str]]:
    """Tick positions (growth multiples) and percent labels for a log-scaled cumulative-return axis."""
    candidates = (0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 500.0, 1000.0)
    low = min(float(curve.min()) for curve in curves)
    high = max(float(curve.max()) for curve in curves)
    ticks = [value for value in candidates if low * 0.8 <= value <= high * 1.25]
    return ticks, [f"{value - 1.0:,.0%}" for value in ticks]


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

    Args:
        data: Series or DataFrame to plot.
        columns: Column name(s) or shell-style pattern(s) (e.g. ``"*_ret"``)
            to select. Defaults to all columns.
        title: Figure title. Defaults to the column name (single column) or
            a generic title (multiple columns).
        yaxis_title: Y-axis label.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
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
    series = _simple_returns(returns, return_type)
    curve = ((1.0 + series).cumprod() - 1.0).rename(label or series.name or "Equity")
    figure = line(curve, title=title, yaxis_title="Cumulative return", height=height)
    figure.add_hline(y=0.0, line={"color": "#6B7280", "width": 1, "dash": "dash"})
    figure.update_yaxes(tickformat=".0%")
    return figure


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
    series = _simple_returns(returns, return_type)
    curve = (1.0 + series).cumprod()
    # clip to the implicit starting capital of 1.0 so a first-period loss is captured
    underwater = curve.div(curve.cummax().clip(lower=1.0)).sub(1.0)
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
    reference: pd.Series | None = None
    if benchmark is not None:
        strategy, reference = _aligned_returns(returns, benchmark, return_type)
    else:
        strategy = _simple_returns(returns, return_type, "Strategy")

    strategy_curve = (1.0 + strategy).cumprod()
    # clip to the implicit starting capital of 1.0 so a first-period loss is captured
    strategy_drawdown = strategy_curve.div(strategy_curve.cummax().clip(lower=1.0)).sub(1.0)
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
        y=strategy_curve - 1.0,
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
            y=benchmark_curve - 1.0,
            mode="lines",
            name=reference.name or "Benchmark",
            line={"color": _QUANT_COLORS[1], "width": 2},
            row=1,
            col=1,
        )
    figure.add_hline(y=0.0, line={"color": "#6B7280", "width": 1, "dash": "dash"}, row=1, col=1)
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
    figure.update_yaxes(title_text="Cumulative return", tickformat=".0%", row=1, col=1)
    figure.update_yaxes(title_text="Drawdown", tickformat=".0%", row=2, col=1)
    return figure


def monthly_heatmap(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    title: str = "Monthly returns",
    height: int | None = None,
) -> Figure:
    """Create an interactive, annotated calendar-month return heatmap.

    Args:
        returns: Periodic return series with a ``DatetimeIndex``.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        title: Figure title.
        height: Figure height in pixels. Defaults to a size based on the
            number of years.

    Returns:
        A Plotly ``Figure``.
    """
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
    # Match the compact per-year sizing used for this same panel inside report()'s tearsheet;
    # _base_layout's default top+bottom margins (90 + 50) sit outside that plotting area.
    _base_layout(figure, title=title, height=height or _monthly_heatmap_row_height(len(table)) + 140, time_axis=False)
    figure.update_layout(hovermode="closest")
    figure.update_xaxes(side="top")
    figure.update_yaxes(autorange="reversed", showgrid=False, title_text="")
    return figure


#: Metrics-table rows rendered as percentages; everything else defaults to a
#: 2-decimal number except the explicit int/date rows below.
_METRIC_PCT_ROWS = frozenset(
    {
        "Risk-Free Rate", "Time in Market",
        "Cumulative Return", "CAGR", "Expected Daily", "Expected Monthly", "Expected Yearly",
        "Prob. Sharpe Ratio",
        "Volatility (ann.)", "Daily Value-at-Risk", "Expected Shortfall (cVaR)", "Kelly Criterion", "Risk of Ruin",
        "Max Drawdown", "Avg. Drawdown",
        "MTD", "3M", "6M", "YTD", "1Y", "3Y (ann.)", "5Y (ann.)", "10Y (ann.)", "All-time (ann.)",
        "Best Day", "Worst Day", "Best Month", "Worst Month", "Best Year", "Worst Year",
        "Win Days", "Win Month", "Win Quarter", "Win Year", "Avg. Up Month", "Avg. Down Month",
        "Alpha", "Tracking Error", "Treynor Ratio",
    }
)
_METRIC_INT_ROWS = frozenset({"Longest DD Days", "Avg. Drawdown Days", "Max Consecutive Wins", "Max Consecutive Losses"})


def _format_metric(name: str, value: object) -> str:
    """Format a metrics-table value for display based on its conventional unit."""
    if isinstance(value, pd.Timestamp):
        return "-" if pd.isna(value) else value.strftime("%Y-%m-%d")
    if value is None or pd.isna(value):
        return "-"
    number = float(value)
    if not np.isfinite(number):
        return "-"
    if name in _METRIC_PCT_ROWS:
        return f"{number:.2%}"
    if name in _METRIC_INT_ROWS:
        return f"{number:.0f}"
    return f"{number:.2f}"


def _metrics_frame(
    strategy: pd.Series,
    reference: pd.Series | None,
    *,
    periods_per_year: int,
    rf: float,
    mode: Literal["basic", "full"] = "full",
) -> pd.DataFrame:
    """Build the formatted metrics table, with blank spacer rows between sections."""
    raw = metrics_stats(strategy, reference, mode=mode, periods_per_year=periods_per_year, rf=rf)
    spacer = pd.DataFrame({column: [""] for column in raw.columns}, index=[""])
    blocks: list[pd.DataFrame] = []
    for _, section in raw.groupby(level="Section", sort=False):
        if blocks:
            blocks.append(spacer)
        metric_names = section.index.get_level_values("Metric")
        blocks.append(
            pd.DataFrame(
                {column: [_format_metric(name, value) for name, value in zip(metric_names, section[column])] for column in raw.columns},
                index=metric_names,
            )
        )
    return pd.concat(blocks)


def metrics_table(
    returns: pd.Series,
    *,
    benchmark: pd.Series | None = None,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
    rf: float = 0.0,
    mode: Literal["basic", "full"] = "full",
    title: str = "Key Performance Metrics",
    height: int | None = None,
) -> Figure:
    """Create an interactive table of performance metrics.

    Args:
        returns: Strategy periodic return series.
        benchmark: Optional benchmark periodic return series, aligned to
            ``returns`` on shared dates. Adds a benchmark column plus
            relative rows (Beta, Alpha, Correlation, R², Information Ratio,
            Tracking Error, Treynor Ratio) when given.
        return_type: Whether ``returns``/``benchmark`` are ``"simple"`` or
            ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.
        rf: Annualized risk-free rate. Defaults to ``0.0``.
        mode: ``"full"`` (default) for the complete quantstats-style metric
            set, ``"basic"`` for a compact headline subset. See
            :func:`qrt.stats.metrics`.
        title: Figure title.
        height: Figure height in pixels. Defaults to a size based on the
            number of metric rows.

    Returns:
        A Plotly ``Figure``.
    """
    if benchmark is not None:
        strategy, reference = _aligned_returns(returns, benchmark, return_type)
    else:
        strategy, reference = _simple_returns(returns, return_type, "Strategy"), None
    periods = _periods_per_year(periods_per_year, strategy.index)
    frame = _metrics_frame(strategy, reference, periods_per_year=periods, rf=rf, mode=mode)

    figure = go.Figure(
        go.Table(
            header={"values": ["Metric", *frame.columns], "align": "left", "fill_color": "#F3F4F6", "font": {"size": 12}},
            cells={"values": [frame.index, *[frame[column] for column in frame.columns]], "align": "left", "fill_color": "white"},
            columnwidth=[2, *([1] * len(frame.columns))],
        )
    )
    _base_layout(figure, title=title, height=height or max(320, 20 * len(frame) + 140), time_axis=False)
    return figure


def cumulative_returns(
    returns: pd.Series,
    *,
    benchmark: pd.Series | None = None,
    return_type: ReturnType = "simple",
    scale: Literal["linear", "log", "volatility_matched"] = "linear",
    title: str | None = None,
    height: int = 400,
) -> Figure:
    """Create an interactive cumulative-returns chart, strategy vs an optional benchmark.

    Args:
        returns: Strategy periodic return series.
        benchmark: Optional benchmark periodic return series, aligned to
            ``returns`` on shared dates.
        return_type: Whether ``returns``/``benchmark`` are ``"simple"`` or
            ``"log"`` returns.
        scale: ``"linear"`` (plain cumulative percentage returns), ``"log"``
            (log y-axis with percent tick labels, to compare compounding
            regimes across very different magnitudes), or
            ``"volatility_matched"`` (rescales the benchmark's returns to
            match the strategy's volatility before compounding, isolating
            differences in trend from differences in risk taken). The latter
            requires ``benchmark``.
        title: Figure title.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    if benchmark is not None:
        strategy, reference = _aligned_returns(returns, benchmark, return_type)
    else:
        strategy, reference = _simple_returns(returns, return_type, "Strategy"), None
        if scale == "volatility_matched":
            raise ValueError("scale='volatility_matched' requires a benchmark")

    if scale == "volatility_matched" and reference is not None:
        strategy_vol, benchmark_vol = strategy.std(ddof=1), reference.std(ddof=1)
        if benchmark_vol:
            reference = (reference * (strategy_vol / benchmark_vol)).rename(reference.name)

    figure = go.Figure()
    strategy_curve = (1.0 + strategy).cumprod()
    reference_curve = (1.0 + reference).cumprod() if reference is not None else None
    offset = 0.0 if scale == "log" else 1.0
    if reference_curve is not None:
        figure.add_scatter(
            x=reference_curve.index, y=reference_curve - offset, mode="lines", name=reference.name or "Benchmark",
            line={"color": _QUANT_COLORS[1], "width": 2},
        )
    figure.add_scatter(
        x=strategy_curve.index, y=strategy_curve - offset, mode="lines", name=strategy.name or "Strategy",
        line={"color": _QUANT_COLORS[0], "width": 2},
    )
    figure.add_hline(y=1.0 - offset, line={"color": "#6B7280", "width": 1, "dash": "dash"})

    default_titles = {
        "linear": "Cumulative Returns vs Benchmark" if reference is not None else "Cumulative Returns",
        "log": "Cumulative Returns vs Benchmark (Log Scaled)" if reference is not None else "Cumulative Returns (Log Scaled)",
        "volatility_matched": "Cumulative Returns vs Benchmark (Volatility Matched)",
    }
    _base_layout(figure, title=title or default_titles[scale], height=height)
    _set_date_range(figure, strategy_curve.index)
    if scale == "log":
        curves = [strategy_curve] if reference_curve is None else [strategy_curve, reference_curve]
        tickvals, ticktext = _log_percent_ticks(*curves)
        figure.update_yaxes(title_text="Cumulative return", type="log", tickvals=tickvals, ticktext=ticktext)
    else:
        figure.update_yaxes(title_text="Cumulative return", tickformat=".0%")
    return figure


def _yearly_frame(strategy: pd.Series, reference: pd.Series | None) -> pd.DataFrame:
    """Build a year-indexed table of compounded yearly returns, one column per series."""
    strategy_yearly = aggregate_returns(strategy, "Y")
    strategy_yearly.index = strategy_yearly.index.year
    frame = pd.DataFrame({strategy.name or "Strategy": strategy_yearly})
    if reference is not None:
        reference_yearly = aggregate_returns(reference, "Y")
        reference_yearly.index = reference_yearly.index.year
        frame.insert(0, reference.name or "Benchmark", reference_yearly)
    frame.index.name = "Year"
    return frame


def eoy_returns(
    returns: pd.Series,
    *,
    benchmark: pd.Series | None = None,
    return_type: ReturnType = "simple",
    title: str | None = None,
    height: int = 400,
) -> Figure:
    """Create an interactive bar chart of compounded end-of-year returns.

    Args:
        returns: Strategy periodic return series.
        benchmark: Optional benchmark periodic return series, aligned to
            ``returns`` on shared dates.
        return_type: Whether ``returns``/``benchmark`` are ``"simple"`` or
            ``"log"`` returns.
        title: Figure title.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    if benchmark is not None:
        strategy, reference = _aligned_returns(returns, benchmark, return_type)
    else:
        strategy, reference = _simple_returns(returns, return_type, "Strategy"), None
    frame = _yearly_frame(strategy, reference)

    figure = go.Figure()
    for index, column in enumerate(frame.columns):
        figure.add_bar(x=frame.index.astype(str), y=frame[column], name=str(column), marker_color=_QUANT_COLORS[index % len(_QUANT_COLORS)])
    figure.add_hline(y=frame[strategy.name or "Strategy"].mean(), line={"color": "#6B7280", "width": 1, "dash": "dash"})
    default_title = "EOY Returns vs Benchmark" if reference is not None else "EOY Returns"
    _base_layout(figure, title=title or default_title, height=height, time_axis=False)
    figure.update_xaxes(type="category", title_text="Year")
    figure.update_yaxes(title_text="Return", tickformat=".0%")
    return figure


def monthly_distribution(
    returns: pd.Series,
    *,
    benchmark: pd.Series | None = None,
    return_type: ReturnType = "simple",
    title: str = "Distribution of Monthly Returns",
    height: int = 400,
) -> Figure:
    """Create an interactive histogram of compounded monthly returns.

    Args:
        returns: Strategy periodic return series.
        benchmark: Optional benchmark periodic return series, aligned to
            ``returns`` on shared dates, overlaid as a second histogram.
        return_type: Whether ``returns``/``benchmark`` are ``"simple"`` or
            ``"log"`` returns.
        title: Figure title.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    if benchmark is not None:
        strategy, reference = _aligned_returns(returns, benchmark, return_type)
    else:
        strategy, reference = _simple_returns(returns, return_type, "Strategy"), None

    figure = go.Figure()
    if reference is not None:
        figure.add_histogram(x=aggregate_returns(reference, "M") * 100, name=reference.name or "Benchmark", marker_color=_QUANT_COLORS[1], opacity=0.65)
    figure.add_histogram(x=aggregate_returns(strategy, "M") * 100, name=strategy.name or "Strategy", marker_color=_QUANT_COLORS[0], opacity=0.65)
    figure.update_layout(barmode="overlay" if reference is None else "group")
    _base_layout(figure, title=title, height=height, time_axis=False)
    figure.update_xaxes(title_text="Monthly return", ticksuffix="%")
    figure.update_yaxes(title_text="Frequency")
    return figure


def daily_returns(
    returns: pd.Series,
    *,
    benchmark: pd.Series | None = None,
    return_type: ReturnType = "simple",
    active: bool = False,
    title: str | None = None,
    height: int = 320,
) -> Figure:
    """Create an interactive bar chart of periodic returns over time.

    Args:
        returns: Strategy periodic return series.
        benchmark: Benchmark periodic return series, aligned to ``returns``
            on shared dates. Required when ``active=True``.
        return_type: Whether ``returns``/``benchmark`` are ``"simple"`` or
            ``"log"`` returns.
        active: Plot active returns (``returns - benchmark``) instead of raw
            returns. Requires ``benchmark``.
        title: Figure title.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    if active and benchmark is None:
        raise ValueError("active=True requires a benchmark")
    if benchmark is not None:
        strategy, reference = _aligned_returns(returns, benchmark, return_type)
    else:
        strategy, reference = _simple_returns(returns, return_type, "Strategy"), None
    series = (strategy - reference).rename(strategy.name) if active and reference is not None else strategy

    figure = go.Figure(go.Bar(x=series.index, y=series, name=series.name or "Returns", marker_color=_QUANT_COLORS[0]))
    _base_layout(figure, title=title or ("Daily Active Returns" if active else "Daily Returns"), height=height)
    _set_date_range(figure, series.index)
    figure.update_yaxes(title_text="Return", tickformat=".0%")
    return figure


def rolling_volatility(
    returns: pd.Series,
    *,
    benchmark: pd.Series | None = None,
    window: int = 126,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
    title: str = "Rolling Volatility (6-Months)",
    height: int = 320,
) -> Figure:
    """Create an interactive chart of annualized rolling volatility.

    See :func:`qrt.stats.rolling_volatility` for the underlying calculation.

    Args:
        returns: Strategy periodic return series.
        benchmark: Optional benchmark periodic return series, aligned to
            ``returns`` on shared dates, overlaid as a second line.
        window: Rolling window size, in periods.
        return_type: Whether ``returns``/``benchmark`` are ``"simple"`` or
            ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.
        title: Figure title.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    if benchmark is not None:
        strategy, reference = _aligned_returns(returns, benchmark, return_type)
    else:
        strategy, reference = _simple_returns(returns, return_type, "Strategy"), None
    series = rolling_volatility_stats(strategy, window, periods_per_year=periods_per_year)

    figure = go.Figure(go.Scatter(x=series.index, y=series, mode="lines", name=strategy.name or "Strategy", line={"color": _QUANT_COLORS[0], "width": 1.6}))
    if reference is not None:
        bench_series = rolling_volatility_stats(reference, window, periods_per_year=periods_per_year)
        figure.add_scatter(x=bench_series.index, y=bench_series, mode="lines", name=reference.name or "Benchmark", line={"color": _QUANT_COLORS[1], "width": 1.6})
    _base_layout(figure, title=title, height=height)
    _set_date_range(figure, series.index)
    figure.update_yaxes(title_text="Volatility (ann.)", tickformat=".0%")
    return figure


def rolling_sharpe(
    returns: pd.Series,
    *,
    window: int = 126,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
    rf: float = 0.0,
    title: str = "Rolling Sharpe (6-Months)",
    height: int = 320,
) -> Figure:
    """Create an interactive chart of annualized rolling Sharpe ratio.

    See :func:`qrt.stats.rolling_sharpe` for the underlying calculation.

    Args:
        returns: Periodic return series.
        window: Rolling window size, in periods.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.
        rf: Annualized risk-free rate. Defaults to ``0.0``.
        title: Figure title.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    series = rolling_sharpe_stats(returns, window, return_type=return_type, periods_per_year=periods_per_year, rf=rf)
    figure = go.Figure(go.Scatter(x=series.index, y=series, mode="lines", name="Sharpe", line={"color": _QUANT_COLORS[0], "width": 1.6}))
    figure.add_hline(y=0.0, line={"color": "#6B7280", "width": 1, "dash": "dash"})
    _base_layout(figure, title=title, height=height)
    _set_date_range(figure, series.index)
    figure.update_yaxes(title_text="Sharpe")
    return figure


def rolling_sortino(
    returns: pd.Series,
    *,
    window: int = 126,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
    rf: float = 0.0,
    title: str = "Rolling Sortino (6-Months)",
    height: int = 320,
) -> Figure:
    """Create an interactive chart of annualized rolling Sortino ratio.

    See :func:`qrt.stats.rolling_sortino` for the underlying calculation.

    Args:
        returns: Periodic return series.
        window: Rolling window size, in periods.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.
        rf: Annualized risk-free rate. Defaults to ``0.0``.
        title: Figure title.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    series = rolling_sortino_stats(returns, window, return_type=return_type, periods_per_year=periods_per_year, rf=rf)
    figure = go.Figure(go.Scatter(x=series.index, y=series, mode="lines", name="Sortino", line={"color": _QUANT_COLORS[0], "width": 1.6}))
    figure.add_hline(y=0.0, line={"color": "#6B7280", "width": 1, "dash": "dash"})
    _base_layout(figure, title=title, height=height)
    _set_date_range(figure, series.index)
    figure.update_yaxes(title_text="Sortino")
    return figure


def rolling_beta(
    returns: pd.Series,
    benchmark: pd.Series,
    *,
    return_type: ReturnType = "simple",
    windows: tuple[int, int] = (126, 252),
    title: str = "Rolling Beta to Benchmark",
    height: int = 320,
) -> Figure:
    """Create an interactive chart of rolling beta over two windows (e.g. 6- and 12-month).

    See :func:`qrt.stats.rolling_beta` for the underlying calculation.

    Args:
        returns: Strategy periodic return series.
        benchmark: Benchmark periodic return series, aligned to ``returns``
            on shared dates.
        return_type: Whether ``returns``/``benchmark`` are ``"simple"`` or
            ``"log"`` returns.
        windows: Pair of rolling window sizes, in periods (shorter first).
        title: Figure title.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    labels = {windows[0]: "6-Months", windows[1]: "12-Months"}
    figure = go.Figure()
    first_index: pd.Index | None = None
    for index, window in enumerate(windows):
        series = rolling_beta_stats(returns, benchmark, window, return_type=return_type)
        first_index = first_index if first_index is not None else series.index
        figure.add_scatter(
            x=series.index, y=series, mode="lines", name=labels.get(window, f"{window}-period"),
            line={"color": _QUANT_COLORS[index % len(_QUANT_COLORS)], "width": 1.6 if index == 0 else 1.1},
        )
    figure.add_hline(y=1.0, line={"color": "#6B7280", "width": 1, "dash": "dash"})
    _base_layout(figure, title=title, height=height)
    _set_date_range(figure, first_index)
    figure.update_yaxes(title_text="Beta")
    return figure


def factor_loadings(
    returns: pd.Series,
    factors: pd.DataFrame,
    *,
    return_type: ReturnType = "simple",
    rf: str | pd.Series | None = "RF",
    covariance: CovarianceType = "nonrobust",
    confidence_level: float = 0.95,
    include_alpha: bool = False,
    title: str = "Factor Loadings",
    height: int = 400,
) -> Figure:
    """Create an interactive bar chart of full-period multi-factor regression coefficients.

    See :func:`qrt.stats.factor_regression` for the underlying calculation, e.g. the
    Fama-French five-factor model's ``Mkt-RF``/``SMB``/``HML``/``RMW``/``CMA`` betas.

    Args:
        returns: Strategy periodic return series.
        factors: DataFrame of periodic factor return columns, aligned to ``returns``.
        return_type: Whether ``returns`` is ``"simple"`` or ``"log"`` returns.
        rf: See :func:`qrt.stats.factor_regression`.
        covariance: Standard-error estimator; see :func:`qrt.stats.factor_regression`.
        confidence_level: Confidence level for the error bars. Defaults to ``0.95``.
        include_alpha: Whether to include the ``Alpha`` bar alongside the factor
            betas. Defaults to ``False`` since alpha's scale/units usually differ
            from a factor beta (see :func:`qrt.stats.factor_regression_stats`
            for alpha shown on its own, annualized).
        title: Figure title.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    table = factor_regression_stats(
        returns, factors, return_type=return_type, rf=rf, covariance=covariance, confidence_level=confidence_level
    )
    if not include_alpha:
        table = table.drop("Alpha")

    colors = ["#54A24B" if value >= 0 else "#E45756" for value in table["Coefficient"]]
    figure = go.Figure(
        go.Bar(
            x=table.index.astype(str),
            y=table["Coefficient"],
            marker_color=colors,
            error_y={
                "type": "data",
                "array": table["CI Upper"] - table["Coefficient"],
                "arrayminus": table["Coefficient"] - table["CI Lower"],
                "visible": True,
            },
            text=[f"{value:+.2f}" for value in table["Coefficient"]],
            textposition="outside",
            customdata=table[["p-Value"]],
            hovertemplate="%{x}<br>Coefficient: %{y:.3f}<br>p-value: %{customdata[0]:.3f}<extra></extra>",
        )
    )
    figure.add_hline(y=0.0, line={"color": "#6B7280", "width": 1, "dash": "dash"})
    _base_layout(figure, title=title, height=height, time_axis=False)
    figure.update_yaxes(title_text="Coefficient (β)")
    return figure


def rolling_factor_betas(
    returns: pd.Series,
    factors: pd.DataFrame,
    window: int = 63,
    *,
    return_type: ReturnType = "simple",
    rf: str | pd.Series | None = "RF",
    min_observations: int | None = None,
    title: str | None = None,
    height: int = 380,
) -> Figure:
    """Create an interactive chart of rolling multi-factor betas over time.

    See :func:`qrt.stats.rolling_factor_regression` for the underlying calculation,
    e.g. the rolling Fama-French five-factor betas that reveal time-varying exposure.

    Args:
        returns: Strategy periodic return series.
        factors: DataFrame of periodic factor return columns, aligned to ``returns``.
        window: Trailing window size, in periods. Defaults to ``63`` (~3 trading months).
        return_type: Whether ``returns`` is ``"simple"`` or ``"log"`` returns.
        rf: See :func:`qrt.stats.factor_regression`.
        min_observations: See :func:`qrt.stats.rolling_factor_regression`.
        title: Figure title. Defaults to a title naming ``window``.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``. Each factor's hover also shows that window's
        observation count and R², to distinguish real exposure changes from
        noisy/short-window estimation.
    """
    table = rolling_factor_regression_stats(
        returns, factors, window, return_type=return_type, rf=rf, min_observations=min_observations
    )
    factor_columns = [column for column in table.columns if column not in ("Alpha", "R²", "N Obs")]
    hover_extra = np.column_stack([table["N Obs"], table["R²"]])

    figure = go.Figure()
    for index, column in enumerate(factor_columns):
        figure.add_scatter(
            x=table.index,
            y=table[column],
            mode="lines",
            name=str(column),
            line={"color": _QUANT_COLORS[index % len(_QUANT_COLORS)], "width": 1.6},
            customdata=hover_extra,
            hovertemplate=(
                f"{column} β: " + "%{y:.2f}<br>Window observations: %{customdata[0]:.0f}"
                "<br>Window R²: %{customdata[1]:.2f}<extra></extra>"
            ),
        )
    figure.add_hline(y=0.0, line={"color": "#6B7280", "width": 1, "dash": "dash"})
    _base_layout(figure, title=title or f"Rolling Factor Betas ({window}-period window)", height=height)
    _set_date_range(figure, table.index)
    figure.update_yaxes(title_text="Beta")
    return figure


def factor_contributions(
    returns: pd.Series,
    factors: pd.DataFrame,
    *,
    return_type: ReturnType = "simple",
    rf: str | pd.Series | None = "RF",
    covariance: CovarianceType = "nonrobust",
    title: str = "Cumulative Factor Contribution",
    height: int = 400,
) -> Figure:
    """Create an interactive stacked-area chart of cumulative factor return contributions.

    See :func:`qrt.stats.factor_contributions` for the underlying per-period return
    attribution (alpha + one term per factor + residual, from a full-period fit).
    Cumulative sums are *arithmetic* (not compounded), so the stacked areas always
    add up exactly to the strategy's cumulative excess return, drawn overlaid as a
    dotted reference line.

    Args:
        returns: Strategy periodic return series.
        factors: DataFrame of periodic factor return columns, aligned to ``returns``.
        return_type: Whether ``returns`` is ``"simple"`` or ``"log"`` returns.
        rf: See :func:`qrt.stats.factor_regression`.
        covariance: See :func:`qrt.stats.factor_regression`.
        title: Figure title.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    contributions = factor_contributions_stats(returns, factors, return_type=return_type, rf=rf, covariance=covariance)
    cumulative = contributions.cumsum()
    total = cumulative.sum(axis=1).rename("Total (Excess Return)")

    figure = go.Figure()
    for index, column in enumerate(cumulative.columns):
        figure.add_scatter(
            x=cumulative.index,
            y=cumulative[column],
            mode="lines",
            name=str(column),
            stackgroup="contributions",
            line={"color": _QUANT_COLORS[index % len(_QUANT_COLORS)], "width": 0.5},
        )
    figure.add_scatter(
        x=total.index, y=total, mode="lines", name=total.name,
        line={"color": "#111827", "width": 2, "dash": "dot"},
    )
    _base_layout(figure, title=title, height=height)
    _set_date_range(figure, cumulative.index)
    figure.update_yaxes(title_text="Cumulative contribution", tickformat=".0%")
    return figure


def worst_drawdowns(
    returns: pd.Series,
    *,
    top: int = 5,
    return_type: ReturnType = "simple",
    title: str | None = None,
    height: int = 400,
) -> Figure:
    """Create an equity curve with the worst drawdown periods shaded.

    See :func:`qrt.stats.drawdown_details` for the underlying episode breakdown.

    Args:
        returns: Periodic return series.
        top: Number of worst (deepest) drawdown episodes to shade.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        title: Figure title.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    series = _simple_returns(returns, return_type)
    curve = (1.0 + series).cumprod() - 1.0
    episodes = drawdown_details(series, sort_by="depth").head(top)

    figure = go.Figure(go.Scatter(x=curve.index, y=curve, mode="lines", name=series.name or "Strategy", line={"color": _QUANT_COLORS[0], "width": 2}))
    for _, episode in episodes.iterrows():
        figure.add_vrect(x0=episode["Start"].isoformat(), x1=episode["End"].isoformat(), layer="below", line_width=0, fillcolor="#E45756", opacity=0.15)
    _base_layout(figure, title=title or f"Worst {top} Drawdown Periods", height=height)
    _set_date_range(figure, curve.index)
    figure.update_yaxes(title_text="Cumulative return", tickformat=".0%")
    return figure


def return_quantiles(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    title: str = "Return Quantiles",
    height: int = 400,
) -> Figure:
    """Create box plots comparing return distributions across compounding periods.

    See :func:`qrt.stats.distribution` for the underlying period buckets.

    Args:
        returns: Periodic return series.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        title: Figure title.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    buckets = distribution_stats(returns, return_type=return_type)
    figure = go.Figure()
    for index, (period, data) in enumerate(buckets.items()):
        values = [value * 100 for value in (*data["values"], *data["outliers"])]
        figure.add_box(y=values, name=period, marker={"color": _QUANT_COLORS[index % len(_QUANT_COLORS)]}, boxpoints="outliers")
    _base_layout(figure, title=title, height=height, time_axis=False)
    figure.update_yaxes(title_text="Return", ticksuffix="%")
    return figure


def report(
    returns: pd.Series,
    *,
    benchmark: pd.Series | None = None,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
    rf: float = 0.0,
    mode: Literal["basic", "full"] = "full",
    worst_drawdowns_count: int = 5,
    title: str | None = None,
) -> Figure:
    """Create a full quantstats-style multi-panel strategy tearsheet.

    Lays out a chart column (cumulative-returns variants, EOY returns, return
    distributions, rolling risk diagnostics, drawdown analysis, a monthly
    heatmap) alongside a table column (key metrics, EOY returns, worst
    drawdowns) in a single scrollable Plotly figure. Individual panels are
    also available standalone (:func:`metrics_table`, :func:`cumulative_returns`,
    :func:`eoy_returns`, :func:`monthly_distribution`, :func:`daily_returns`,
    :func:`rolling_volatility`, :func:`rolling_sharpe`, :func:`rolling_sortino`,
    :func:`rolling_beta`, :func:`worst_drawdowns`, :func:`drawdown`,
    :func:`monthly_heatmap`, :func:`return_quantiles`).

    Args:
        returns: Strategy periodic return series.
        benchmark: Optional benchmark periodic return series, aligned to
            ``returns`` on shared dates. Adds benchmark overlays/columns and
            benchmark-relative panels (volatility-matched returns, rolling
            beta) throughout.
        return_type: Whether ``returns``/``benchmark`` are ``"simple"`` or
            ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.
        rf: Annualized risk-free rate. Defaults to ``0.0``.
        mode: ``"full"`` (default) for the complete quantstats-style metrics
            table, ``"basic"`` for a compact headline subset. See
            :func:`qrt.stats.metrics`.
        worst_drawdowns_count: Number of worst drawdown episodes to shade/list.
        title: Figure title.

    Returns:
        A single tall Plotly ``Figure`` stacking every tearsheet panel.
    """
    if benchmark is not None:
        strategy, reference = _aligned_returns(returns, benchmark, return_type)
    else:
        strategy, reference = _simple_returns(returns, return_type, "Strategy"), None
    periods = _periods_per_year(periods_per_year, strategy.index)
    strategy_name = strategy.name or "Strategy"
    has_benchmark = reference is not None

    metrics_frame = _metrics_frame(strategy, reference, periods_per_year=periods, rf=rf, mode=mode)
    yearly_frame = _yearly_frame(strategy, reference)
    dd_episodes = drawdown_details(strategy, sort_by="depth")
    dd_table_frame = dd_episodes.head(10).copy()
    if not dd_table_frame.empty:
        dd_table_frame["Start"] = dd_table_frame["Start"].dt.date.astype(str)
        dd_table_frame["End"] = dd_table_frame["End"].dt.date.astype(str)
        dd_table_frame["Max Drawdown"] = dd_table_frame["Max Drawdown"].map(lambda value: f"{value:.2%}")

    # left column: charts, top to bottom, mirroring the quantstats layout. (subplot title, kind, pixel height)
    rows: list[tuple[str, str, int]] = [
        ("Cumulative Returns vs Benchmark" if has_benchmark else "Cumulative Returns", "cumulative_linear", 280),
        ("Cumulative Returns vs Benchmark (Log Scaled)" if has_benchmark else "Cumulative Returns (Log Scaled)", "cumulative_log", 280),
    ]
    if has_benchmark:
        rows.append(("Cumulative Returns vs Benchmark (Volatility Matched)", "cumulative_volmatch", 280))
    rows.append(("EOY Returns vs Benchmark" if has_benchmark else "EOY Returns", "eoy_bar", 280))
    rows.append(("Distribution of Monthly Returns", "monthly_dist", 280))
    rows.append(("Daily Returns", "daily_returns", 220))
    if has_benchmark:
        rows.append(("Rolling Beta to Benchmark", "rolling_beta", 220))
    rows.append(("Rolling Volatility (6-Months)", "rolling_vol", 220))
    rows.append(("Rolling Sharpe (6-Months)", "rolling_sharpe", 220))
    rows.append(("Rolling Sortino (6-Months)", "rolling_sortino", 220))
    rows.append((f"Worst {worst_drawdowns_count} Drawdown Periods", "worst_dd", 280))
    rows.append(("Underwater Plot", "underwater", 220))
    rows.append(("Monthly Returns", "heatmap", _monthly_heatmap_row_height(len(monthly_returns(strategy)))))

    # left column: chart subplots with real gaps between rows; right column: no
    # subplots — the three tables are content-sized and placed via explicit paper
    # domains anchored to the top, mirroring quantstats' dense side column.
    n_rows = len(rows)
    gap_px = 80
    margin_top, margin_bottom = 100, 50
    total_height = sum(height for _, _, height in rows) + gap_px * (n_rows - 1)
    plot_area = total_height - margin_top - margin_bottom
    horizontal_spacing = 0.06

    figure = make_subplots(
        rows=n_rows,
        cols=2,
        column_widths=[0.66, 0.34],
        specs=[[{"type": "xy"}, None] for _ in range(n_rows)],
        subplot_titles=[row_title for row_title, _, _ in rows],
        horizontal_spacing=horizontal_spacing,
        vertical_spacing=gap_px / plot_area,
        row_heights=[height for _, _, height in rows],
    )

    eoy_table_frame = yearly_frame.reset_index()
    for column in yearly_frame.columns:
        eoy_table_frame[column] = eoy_table_frame[column].map(lambda value: f"{value:.2%}")
    if has_benchmark:
        benchmark_name = reference.name or "Benchmark"
        multiplier = yearly_frame[strategy_name].to_numpy() / np.where(
            yearly_frame[benchmark_name].to_numpy() == 0.0, np.nan, yearly_frame[benchmark_name].to_numpy()
        )
        eoy_table_frame["Multiplier"] = [f"{value:.2f}" if np.isfinite(value) else "-" for value in multiplier]
        eoy_table_frame["Won"] = np.where(yearly_frame[strategy_name].to_numpy() >= yearly_frame[benchmark_name].to_numpy(), "✓", "✗")

    header_px, cell_px = 28, 24
    right_x0 = 0.66 * (1 - horizontal_spacing) + horizontal_spacing
    table_blocks = [
        (
            "Key Performance Metrics",
            ["Metric", *metrics_frame.columns],
            [metrics_frame.index, *[metrics_frame[column] for column in metrics_frame.columns]],
            len(metrics_frame) + 3,  # slack rows: long labels wrap to two lines in the narrow column
            [2, *([1] * len(metrics_frame.columns))],
        ),
        (
            "EOY Returns vs Benchmark" if has_benchmark else "EOY Returns",
            list(eoy_table_frame.columns),
            [eoy_table_frame[column] for column in eoy_table_frame.columns],
            len(eoy_table_frame),
            None,
        ),
        (
            f"Worst {len(dd_table_frame)} Drawdowns",
            ["Started", "Recovered", "Drawdown", "Days"],
            [dd_table_frame["Start"], dd_table_frame["End"], dd_table_frame["Max Drawdown"], dd_table_frame["Days"]]
            if not dd_table_frame.empty
            else [[], [], [], []],
            len(dd_table_frame),
            None,
        ),
    ]
    y_cursor = 1.0
    for block_title, header_values, cell_values, n_data_rows, column_widths in table_blocks:
        table_px = header_px + cell_px * n_data_rows + 10
        y_bottom = max(0.0, y_cursor - table_px / plot_area)
        figure.add_annotation(
            text=f"<b>{block_title}</b>", x=(right_x0 + 1.0) / 2, y=y_cursor, xref="paper", yref="paper",
            xanchor="center", yanchor="bottom", showarrow=False, font={"size": 16},
        )
        table = go.Table(
            header={"values": header_values, "align": "left", "fill_color": "#F3F4F6", "font": {"size": 12}, "height": header_px},
            cells={"values": cell_values, "align": "left", "fill_color": "white", "height": cell_px},
            domain={"x": [right_x0, 1.0], "y": [y_bottom, y_cursor]},
        )
        if column_widths is not None:
            table.columnwidth = column_widths
        figure.add_trace(table)
        y_cursor = y_bottom - 60.0 / plot_area

    for row_index, (_, kind, _height) in enumerate(rows, start=1):
        if kind in ("cumulative_linear", "cumulative_log", "cumulative_volmatch"):
            series_reference = reference
            if kind == "cumulative_volmatch" and reference is not None:
                strategy_vol, benchmark_vol = strategy.std(ddof=1), reference.std(ddof=1)
                series_reference = (reference * (strategy_vol / benchmark_vol)).rename(reference.name) if benchmark_vol else reference
            offset = 0.0 if kind == "cumulative_log" else 1.0
            strategy_curve = (1.0 + strategy).cumprod()
            reference_curve = (1.0 + series_reference).cumprod() if series_reference is not None else None
            if reference_curve is not None:
                figure.add_scatter(
                    x=reference_curve.index, y=reference_curve - offset, mode="lines", name=series_reference.name or "Benchmark",
                    line={"color": _QUANT_COLORS[1], "width": 2}, showlegend=(kind == "cumulative_linear"),
                    legendgroup="benchmark", row=row_index, col=1,
                )
            figure.add_scatter(
                x=strategy_curve.index, y=strategy_curve - offset, mode="lines", name=strategy_name,
                line={"color": _QUANT_COLORS[0], "width": 2}, showlegend=(kind == "cumulative_linear"),
                legendgroup="strategy", row=row_index, col=1,
            )
            figure.add_hline(
                y=1.0 - offset, line={"color": "#6B7280", "width": 1, "dash": "dash"},
                row=row_index, col=1, exclude_empty_subplots=False,
            )
            _set_date_range(figure, strategy_curve.index, row=row_index, col=1)
            if kind == "cumulative_log":
                curves = [strategy_curve] if reference_curve is None else [strategy_curve, reference_curve]
                tickvals, ticktext = _log_percent_ticks(*curves)
                figure.update_yaxes(title_text="Cumulative return", type="log", tickvals=tickvals, ticktext=ticktext, row=row_index, col=1)
            else:
                figure.update_yaxes(title_text="Cumulative return", tickformat=".0%", row=row_index, col=1)
        elif kind == "eoy_bar":
            for index, column in enumerate(yearly_frame.columns):
                figure.add_bar(
                    x=yearly_frame.index.astype(str), y=yearly_frame[column], name=str(column),
                    marker_color=_QUANT_COLORS[index % len(_QUANT_COLORS)], showlegend=False, row=row_index, col=1,
                )
            figure.update_xaxes(type="category", row=row_index, col=1)
            figure.update_yaxes(title_text="Return", tickformat=".0%", row=row_index, col=1)
        elif kind == "monthly_dist":
            if reference is not None:
                figure.add_histogram(
                    x=aggregate_returns(reference, "M") * 100, name=reference.name or "Benchmark",
                    marker_color=_QUANT_COLORS[1], opacity=0.65, showlegend=False, row=row_index, col=1,
                )
            figure.add_histogram(
                x=aggregate_returns(strategy, "M") * 100, name=strategy_name,
                marker_color=_QUANT_COLORS[0], opacity=0.65, showlegend=False, row=row_index, col=1,
            )
            figure.update_xaxes(title_text="Monthly return", ticksuffix="%", row=row_index, col=1)
            figure.update_yaxes(title_text="Frequency", row=row_index, col=1)
        elif kind == "daily_returns":
            figure.add_bar(x=strategy.index, y=strategy, name=strategy_name, marker_color=_QUANT_COLORS[0], showlegend=False, row=row_index, col=1)
            _set_date_range(figure, strategy.index, row=row_index, col=1)
            figure.update_yaxes(title_text="Return", tickformat=".0%", row=row_index, col=1)
        elif kind == "rolling_beta":
            windows = (126, 252)
            labels = {windows[0]: "6-Months", windows[1]: "12-Months"}
            for index, window in enumerate(windows):
                series = rolling_beta_stats(strategy, reference, window)
                figure.add_scatter(
                    x=series.index, y=series, mode="lines", name=labels[window],
                    line={"color": _QUANT_COLORS[index % len(_QUANT_COLORS)], "width": 1.6 if index == 0 else 1.1},
                    showlegend=False, row=row_index, col=1,
                )
            figure.add_hline(
                y=1.0, line={"color": "#6B7280", "width": 1, "dash": "dash"},
                row=row_index, col=1, exclude_empty_subplots=False,
            )
            _set_date_range(figure, strategy.index, row=row_index, col=1)
            figure.update_yaxes(title_text="Beta", row=row_index, col=1)
        elif kind == "rolling_vol":
            series = rolling_volatility_stats(strategy, 126, periods_per_year=periods)
            figure.add_scatter(x=series.index, y=series, mode="lines", name=strategy_name, line={"color": _QUANT_COLORS[0], "width": 1.6}, showlegend=False, row=row_index, col=1)
            if reference is not None:
                bench_series = rolling_volatility_stats(reference, 126, periods_per_year=periods)
                figure.add_scatter(
                    x=bench_series.index, y=bench_series, mode="lines", name=reference.name or "Benchmark",
                    line={"color": _QUANT_COLORS[1], "width": 1.6}, showlegend=False, row=row_index, col=1,
                )
            _set_date_range(figure, series.index, row=row_index, col=1)
            figure.update_yaxes(title_text="Volatility (ann.)", tickformat=".0%", row=row_index, col=1)
        elif kind == "rolling_sharpe":
            series = rolling_sharpe_stats(strategy, 126, periods_per_year=periods, rf=rf)
            figure.add_scatter(x=series.index, y=series, mode="lines", name="Sharpe", line={"color": _QUANT_COLORS[0], "width": 1.6}, showlegend=False, row=row_index, col=1)
            figure.add_hline(
                y=0.0, line={"color": "#6B7280", "width": 1, "dash": "dash"},
                row=row_index, col=1, exclude_empty_subplots=False,
            )
            _set_date_range(figure, series.index, row=row_index, col=1)
            figure.update_yaxes(title_text="Sharpe", row=row_index, col=1)
        elif kind == "rolling_sortino":
            series = rolling_sortino_stats(strategy, 126, periods_per_year=periods, rf=rf)
            figure.add_scatter(x=series.index, y=series, mode="lines", name="Sortino", line={"color": _QUANT_COLORS[0], "width": 1.6}, showlegend=False, row=row_index, col=1)
            figure.add_hline(
                y=0.0, line={"color": "#6B7280", "width": 1, "dash": "dash"},
                row=row_index, col=1, exclude_empty_subplots=False,
            )
            _set_date_range(figure, series.index, row=row_index, col=1)
            figure.update_yaxes(title_text="Sortino", row=row_index, col=1)
        elif kind == "worst_dd":
            strategy_curve = (1.0 + strategy).cumprod() - 1.0
            figure.add_scatter(
                x=strategy_curve.index, y=strategy_curve, mode="lines", name=strategy_name,
                line={"color": _QUANT_COLORS[0], "width": 2}, showlegend=False, row=row_index, col=1,
            )
            for _, episode in dd_episodes.head(worst_drawdowns_count).iterrows():
                figure.add_vrect(
                    x0=episode["Start"].isoformat(), x1=episode["End"].isoformat(), layer="below", line_width=0,
                    fillcolor="#E45756", opacity=0.15, row=row_index, col=1, exclude_empty_subplots=False,
                )
            _set_date_range(figure, strategy_curve.index, row=row_index, col=1)
            figure.update_yaxes(title_text="Cumulative return", tickformat=".0%", row=row_index, col=1)
        elif kind == "underwater":
            drawdown_curve = to_drawdown_series_(strategy)
            figure.add_scatter(
                x=drawdown_curve.index, y=drawdown_curve, mode="lines", name="Drawdown", fill="tozeroy",
                fillcolor="rgba(228, 87, 86, 0.25)", line={"color": _QUANT_COLORS[3], "width": 1.5}, showlegend=False, row=row_index, col=1,
            )
            _set_date_range(figure, drawdown_curve.index, row=row_index, col=1)
            figure.update_yaxes(title_text="Drawdown", tickformat=".0%", row=row_index, col=1)
        elif kind == "heatmap":
            table = monthly_returns(strategy)
            values = table.to_numpy(dtype=float)
            finite_values = values[np.isfinite(values)]
            limit = max(abs(finite_values.min()), abs(finite_values.max())) if len(finite_values) else 0.01
            text = np.where(np.isfinite(values), np.char.mod("%.1f%%", values * 100), "")
            figure.add_trace(
                go.Heatmap(
                    z=values, x=[pd.Timestamp(2000, month, 1).strftime("%b") for month in table.columns], y=table.index.astype(str),
                    text=text, texttemplate="%{text}", textfont={"size": 10}, colorscale="RdYlGn", zmid=0, zmin=-limit, zmax=limit,
                    showscale=False, hovertemplate="Year %{y}<br>Month %{x}<br>Return %{z:.2%}<extra></extra>",
                ),
                row=row_index, col=1,
            )
            figure.update_yaxes(autorange="reversed", showgrid=False, title_text="", row=row_index, col=1)

    figure.update_layout(
        template="plotly_white",
        title=title or f"{strategy_name} Tearsheet",
        height=total_height,
        showlegend=True,
        legend={"orientation": "h", "y": 1.0, "x": 0, "xanchor": "left", "yanchor": "bottom"},
        margin={"l": 60, "r": 30, "t": margin_top, "b": margin_bottom},
    )
    figure.update_xaxes(showgrid=False)
    figure.update_yaxes(showgrid=True, gridcolor="#E5E7EB", zeroline=False)
    return figure


def montecarlo(
    returns: pd.Series,
    sims: int = 1000,
    *,
    return_type: ReturnType = "simple",
    bust: float | None = None,
    goal: float | None = None,
    confidence: float = 0.95,
    seed: int | None = None,
    block_size: float | None = None,
    periods: int | None = None,
    sample: int = 200,
    title: str | None = None,
    height: int = 520,
) -> Figure:
    """Create an interactive Monte Carlo fan chart of bootstrap-resampled return simulations.

    Runs :func:`qrt.stats.montecarlo` on the full ``sims`` simulations, so the shaded
    confidence band and any ``bust``/``goal`` probabilities reflect the entire sample, then
    renders only a `sample` of the individual paths for readability. Unlike quantstats'
    ``plot_montecarlo`` (which colors paths arbitrarily and, being built on a plain permutation
    of returns, can only vary each path's *shape*, never its terminal value — see the note on
    :func:`qrt.stats.montecarlo`), each rendered path here is colored by its own outcome:

    - **Original** (unresampled) path: bold black line, drawn on top.
    - **Busted** paths (Max Drawdown breached ``bust``): red.
    - **Reached goal** paths (terminal return met ``goal``): green.
    - Everything else: light gray.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        sims: Number of simulated paths to run; statistics use all of them.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        bust: Optional Max Drawdown threshold (e.g. ``-0.2``); breaching paths are colored red.
        goal: Optional cumulative-return threshold (e.g. ``1.0``); paths reaching it are colored
            green and a reference line is drawn at that level.
        confidence: Confidence level for the shaded fan. Defaults to ``0.95``.
        seed: Optional random seed for reproducibility.
        block_size: Optional mean block length (in periods) for a stationary block bootstrap,
            preserving autocorrelation/volatility clustering that i.i.d. resampling destroys.
            See the Note on :func:`qrt.stats.montecarlo`. Defaults to ``None`` (i.i.d.).
        periods: Optional simulation horizon in periods, decoupled from ``len(returns)`` so a
            long, multi-regime history can be used as the resampling pool while each simulated
            path only covers a realistic forward horizon (e.g. ``252`` for one trading year).
            See the Note on :func:`qrt.stats.montecarlo`. Defaults to ``None`` (the full length
            of ``returns``).
        sample: Max number of individual simulated paths rendered (statistics still use all
            ``sims``). Defaults to ``200``.
        title: Figure title. Defaults to ``returns.name``.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    from qrt.stats.core import montecarlo as montecarlo_stats

    result = montecarlo_stats(
        returns,
        sims,
        return_type=return_type,
        bust=bust,
        goal=goal,
        confidence=confidence,
        seed=seed,
        block_size=block_size,
        periods=periods,
    )
    paths: pd.DataFrame = result["paths"]  # type: ignore[assignment]
    band: pd.DataFrame = result["confidence_band"]  # type: ignore[assignment]

    drawdowns = (1.0 + paths).div((1.0 + paths).cummax()).sub(1.0)
    max_drawdowns = drawdowns.min()
    terminal = paths.iloc[-1]

    status = pd.Series("neutral", index=paths.columns)
    if goal is not None:
        status[terminal >= goal] = "goal"
    if bust is not None:
        status[max_drawdowns <= bust] = "bust"

    others = [column for column in paths.columns if column != "sim_0"]
    rng = np.random.default_rng(seed)
    shown = others if len(others) <= sample else list(rng.choice(others, size=sample, replace=False))

    figure = go.Figure()
    figure.add_scatter(
        x=band.index, y=band["Upper"], mode="lines", line={"width": 0}, showlegend=False, hoverinfo="skip"
    )
    figure.add_scatter(
        x=band.index,
        y=band["Lower"],
        mode="lines",
        line={"width": 0},
        fill="tonexty",
        fillcolor="rgba(76, 120, 168, 0.18)",
        name=f"{confidence:.0%} band",
        hoverinfo="skip",
    )

    palette = {
        "neutral": "rgba(148, 163, 184, 0.35)",
        "bust": "rgba(228, 87, 86, 0.55)",
        "goal": "rgba(84, 162, 75, 0.55)",
    }
    labels = {"neutral": "Simulated path", "bust": "Busted", "goal": "Reached goal"}
    seen: set[str] = set()
    for column in shown:
        outcome = status[column]
        figure.add_scatter(
            x=paths.index,
            y=paths[column],
            mode="lines",
            line={"color": palette[outcome], "width": 1},
            name=labels[outcome],
            legendgroup=outcome,
            showlegend=outcome not in seen,
            hoverinfo="skip",
        )
        seen.add(outcome)

    figure.add_scatter(
        x=paths.index, y=paths["sim_0"], mode="lines", name="Original", line={"color": "#111827", "width": 2.6}
    )

    if goal is not None:
        figure.add_hline(y=goal, line={"color": _QUANT_COLORS[2], "width": 1, "dash": "dash"}, annotation_text="Goal")

    stat_bits = []
    if result["bust_probability"] is not None:
        stat_bits.append(f"P(bust) {result['bust_probability']:.1%}")
    if result["goal_probability"] is not None:
        stat_bits.append(f"P(goal) {result['goal_probability']:.1%}")

    chart_title = title or (returns.name or "Monte Carlo simulation")
    _base_layout(figure, title=chart_title, subtitle="  ·  ".join(stat_bits) or None, height=height)
    _set_date_range(figure, paths.index)
    figure.update_yaxes(title_text="Cumulative return", tickformat=".0%")
    return figure


def variance_test(
    trades: pd.Series,
    periods: int,
    sims: int = 1000,
    *,
    return_type: ReturnType = "simple",
    win_rate_variance: float = 0.1,
    ruin: float = -0.9,
    confidence: float = 0.95,
    seed: int | None = None,
    sample: int = 200,
    title: str | None = None,
    height: int = 520,
) -> Figure:
    """Create an interactive Variance Testing fan chart of forward win-rate-varied trade paths.

    Runs :func:`qrt.stats.variance_test` on the full ``sims`` simulations, so the shaded
    confidence band and the make-money/ruin probabilities reflect the entire sample, then renders
    only a ``sample`` of the individual simulated paths for readability, alongside the actual
    historical (``"Real"``) cumulative return over the most recent ``periods`` trades of
    ``trades`` for comparison (truncated to ``periods`` rather than the full history so its
    scale and length stay comparable to the simulated paths):

    - **Real** (actual historical) path: bold black line, drawn on top.
    - **Ruined** paths (Max Drawdown breached ``ruin``): red.
    - **Profitable** paths (positive terminal return): green.
    - Everything else: light gray.

    The simulated paths and confidence band are 0-based when computed (statistics such as
    ``make_money_probability``/``ruin_probability`` stay purely forward-looking, unaffected by
    history), but are rebased for display onto the last ``"Real"`` cumulative return so the fan
    chart continues smoothly from history instead of visually resetting to 0% at "Now" (the
    ``ruin`` reference line is shifted the same way).

    When ``trades`` has a ``DatetimeIndex``, the x-axis shows real calendar dates — the actual
    dates for ``"Real"`` and dates extrapolated forward from the last one for the simulated
    paths (marked with a dotted "Now" line at the boundary) — matching the date axes used
    throughout :mod:`qrt.plot`. Falls back to a plain trade-count axis otherwise.

    Args:
        trades: Per-trade return series (simple or log, per ``return_type``).
        periods: Number of future trades to simulate per path.
        sims: Number of simulated paths to run; statistics use all of them.
        return_type: Whether ``trades`` are ``"simple"`` or ``"log"`` returns.
        win_rate_variance: Amount by which each simulation's win rate is randomly perturbed from
            the historical win rate. See the Args on :func:`qrt.stats.variance_test`.
        ruin: Max Drawdown threshold (e.g. ``-0.9``); breaching paths are colored red and marked
            with a reference line. See the Args on :func:`qrt.stats.variance_test`.
        confidence: Confidence level for the shaded fan. Defaults to ``0.95``.
        seed: Optional random seed for reproducibility.
        sample: Max number of individual simulated paths rendered (statistics still use all
            ``sims``). Defaults to ``200``.
        title: Figure title. Defaults to ``trades.name``.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    from qrt.stats.core import variance_test as variance_test_stats

    result = variance_test_stats(
        trades,
        periods,
        sims,
        return_type=return_type,
        win_rate_variance=win_rate_variance,
        ruin=ruin,
        confidence=confidence,
        seed=seed,
    )
    paths: pd.DataFrame = result["paths"]  # type: ignore[assignment]
    band: pd.DataFrame = result["confidence_band"]  # type: ignore[assignment]
    real_path: pd.Series = result["real_path"]  # type: ignore[assignment]

    drawdowns = (1.0 + paths).div((1.0 + paths).cummax()).sub(1.0)
    max_drawdowns = drawdowns.min()
    terminal = paths.iloc[-1]

    # Simulated paths/band are computed as their own 0-based cumulative return (statistics stay
    # forward-looking, unaffected by history). For display only, rebase them onto the last
    # "Real" level so the fan chart continues smoothly from where history ends instead of
    # visually resetting to 0% at "Now".
    scale = 1.0 + (float(real_path.iloc[-1]) if len(real_path) else 0.0)
    display_paths = (1.0 + paths) * scale - 1.0
    display_band = (1.0 + band) * scale - 1.0
    ruin_level = (1.0 + ruin) * scale - 1.0

    status = pd.Series("neutral", index=paths.columns)
    status[terminal > 0] = "profit"
    status[max_drawdowns <= ruin] = "ruin"

    rng = np.random.default_rng(seed)
    columns = list(paths.columns)
    shown = columns if len(columns) <= sample else list(rng.choice(columns, size=sample, replace=False))

    figure = go.Figure()
    figure.add_scatter(
        x=display_band.index,
        y=display_band["Upper"],
        mode="lines",
        line={"width": 0},
        showlegend=False,
        hoverinfo="skip",
    )
    figure.add_scatter(
        x=display_band.index,
        y=display_band["Lower"],
        mode="lines",
        line={"width": 0},
        fill="tonexty",
        fillcolor="rgba(76, 120, 168, 0.18)",
        name=f"{confidence:.0%} band",
        hoverinfo="skip",
    )

    palette = {
        "neutral": "rgba(148, 163, 184, 0.35)",
        "ruin": "rgba(228, 87, 86, 0.55)",
        "profit": "rgba(84, 162, 75, 0.55)",
    }
    labels = {"neutral": "Random", "ruin": "Ruined", "profit": "Profitable"}
    seen: set[str] = set()
    for column in shown:
        outcome = status[column]
        figure.add_scatter(
            x=display_paths.index,
            y=display_paths[column],
            mode="lines",
            line={"color": palette[outcome], "width": 1},
            name=labels[outcome],
            legendgroup=outcome,
            showlegend=outcome not in seen,
            hoverinfo="skip",
        )
        seen.add(outcome)

    figure.add_scatter(
        x=real_path.index, y=real_path.values, mode="lines", name="Real", line={"color": "#111827", "width": 2.6}
    )
    figure.add_hline(
        y=ruin_level, line={"color": _QUANT_COLORS[3], "width": 1, "dash": "dash"}, annotation_text="Ruin"
    )

    is_dated = isinstance(paths.index, pd.DatetimeIndex)
    if is_dated:
        figure.add_vline(
            x=real_path.index[-1], line={"color": "#9CA3AF", "width": 1, "dash": "dot"}, annotation_text="Now"
        )

    stat_bits = [
        f"Make money {result['make_money_probability']:.1%}",
        f"Ruin odds {result['ruin_probability']:.1%}",
        f"Avg profit {result['average_profit']:.1%}",
        f"Avg drawdown {result['average_drawdown']:.1%}",
        f"PNLDD {result['pnldd_ratio']:.2f}",
    ]

    chart_title = title or (trades.name or "Variance testing")
    _base_layout(figure, title=chart_title, subtitle="  ·  ".join(stat_bits), height=height, time_axis=is_dated)
    if is_dated:
        _set_date_range(figure, real_path.index.append(paths.index))
    else:
        figure.update_xaxes(title_text="Trade #")
    figure.update_yaxes(title_text="Cumulative return", tickformat=".0%")
    return figure


def noise_test(
    returns: pd.Series,
    sims: int = 1000,
    *,
    return_type: ReturnType = "simple",
    noise: float = 0.1,
    bust: float | None = None,
    goal: float | None = None,
    confidence: float = 0.95,
    seed: int | None = None,
    sample: int = 200,
    title: str | None = None,
    height: int = 520,
) -> Figure:
    """Create an interactive Noise Test fan chart of noise-perturbed return path simulations.

    Runs :func:`qrt.stats.noise_test` on the full ``sims`` simulations, so the shaded confidence
    band and any ``bust``/``goal`` probabilities reflect the entire sample, then renders only a
    ``sample`` of the individual perturbed paths for readability. Unlike :func:`montecarlo`
    (which bootstrap-resamples returns, varying their order/composition) or
    :func:`variance_test` (which varies the win rate over a forward horizon), each rendered path
    here keeps the exact historical sequence of ``returns`` but jitters the *magnitude* of every
    period's return by multiplicative noise, testing sensitivity to day-to-day noise/volatility
    rather than resampling variance:

    - **Real** (original, unperturbed) path: bold black line, drawn on top.
    - **Busted** paths (Max Drawdown breached ``bust``): red.
    - **Reached goal** paths (terminal return met ``goal``): green.
    - Everything else: light gray, labeled **Random**.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        sims: Number of simulated paths to run; statistics use all of them.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        noise: Standard deviation of the multiplicative noise applied to each period's return.
            See the Args on :func:`qrt.stats.noise_test`.
        bust: Optional Max Drawdown threshold (e.g. ``-0.2``); breaching paths are colored red.
        goal: Optional cumulative-return threshold (e.g. ``1.0``); paths reaching it are colored
            green and a reference line is drawn at that level.
        confidence: Confidence level for the shaded fan. Defaults to ``0.95``.
        seed: Optional random seed for reproducibility.
        sample: Max number of individual simulated paths rendered (statistics still use all
            ``sims``). Defaults to ``200``.
        title: Figure title. Defaults to ``returns.name``.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    from qrt.stats.core import noise_test as noise_test_stats

    result = noise_test_stats(
        returns,
        sims,
        return_type=return_type,
        noise=noise,
        bust=bust,
        goal=goal,
        confidence=confidence,
        seed=seed,
    )
    paths: pd.DataFrame = result["paths"]  # type: ignore[assignment]
    band: pd.DataFrame = result["confidence_band"]  # type: ignore[assignment]

    drawdowns = (1.0 + paths).div((1.0 + paths).cummax()).sub(1.0)
    max_drawdowns = drawdowns.min()
    terminal = paths.iloc[-1]

    status = pd.Series("neutral", index=paths.columns)
    if goal is not None:
        status[terminal >= goal] = "goal"
    if bust is not None:
        status[max_drawdowns <= bust] = "bust"

    others = [column for column in paths.columns if column != "sim_0"]
    rng = np.random.default_rng(seed)
    shown = others if len(others) <= sample else list(rng.choice(others, size=sample, replace=False))

    figure = go.Figure()
    figure.add_scatter(
        x=band.index, y=band["Upper"], mode="lines", line={"width": 0}, showlegend=False, hoverinfo="skip"
    )
    figure.add_scatter(
        x=band.index,
        y=band["Lower"],
        mode="lines",
        line={"width": 0},
        fill="tonexty",
        fillcolor="rgba(76, 120, 168, 0.18)",
        name=f"{confidence:.0%} band",
        hoverinfo="skip",
    )

    palette = {
        "neutral": "rgba(148, 163, 184, 0.35)",
        "bust": "rgba(228, 87, 86, 0.55)",
        "goal": "rgba(84, 162, 75, 0.55)",
    }
    labels = {"neutral": "Random", "bust": "Busted", "goal": "Reached goal"}
    seen: set[str] = set()
    for column in shown:
        outcome = status[column]
        figure.add_scatter(
            x=paths.index,
            y=paths[column],
            mode="lines",
            line={"color": palette[outcome], "width": 1},
            name=labels[outcome],
            legendgroup=outcome,
            showlegend=outcome not in seen,
            hoverinfo="skip",
        )
        seen.add(outcome)

    figure.add_scatter(
        x=paths.index, y=paths["sim_0"], mode="lines", name="Real", line={"color": "#111827", "width": 2.6}
    )

    if goal is not None:
        figure.add_hline(y=goal, line={"color": _QUANT_COLORS[2], "width": 1, "dash": "dash"}, annotation_text="Goal")
    if bust is not None:
        figure.add_hline(y=bust, line={"color": _QUANT_COLORS[3], "width": 1, "dash": "dash"}, annotation_text="Bust")

    stat_bits = []
    if result["bust_probability"] is not None:
        stat_bits.append(f"P(bust) {result['bust_probability']:.1%}")
    if result["goal_probability"] is not None:
        stat_bits.append(f"P(goal) {result['goal_probability']:.1%}")

    chart_title = title or (returns.name or "Noise test")
    _base_layout(figure, title=chart_title, subtitle="  ·  ".join(stat_bits) or None, height=height)
    _set_date_range(figure, paths.index)
    figure.update_yaxes(title_text="Cumulative return", tickformat=".0%")
    return figure


def montecarlo_distribution(
    returns: pd.Series,
    sims: int = 1000,
    *,
    return_type: ReturnType = "simple",
    bust: float | None = None,
    goal: float | None = None,
    confidence: float = 0.95,
    seed: int | None = None,
    block_size: float | None = None,
    periods: int | None = None,
    title: str | None = None,
    height: int = 420,
) -> Figure:
    """Create interactive terminal-return and Max Drawdown distributions from a Monte Carlo run.

    Complements :func:`montecarlo`'s fan chart with two histograms, both built from all ``sims``
    simulations: the spread of terminal cumulative returns (reward) side-by-side with the spread
    of each simulation's Max Drawdown (risk). Where quantstats' ``plot_montecarlo_distribution``
    shows only the former, pairing it with the drawdown distribution surfaces the downside risk
    a single terminal-value histogram hides. This distinction matters more than it first appears:
    since :func:`qrt.stats.montecarlo` resamples *with replacement*, the terminal-return panel
    here carries real information (a plain permutation-based simulation, as used by quantstats,
    cannot vary the terminal value at all — see the note on :func:`qrt.stats.montecarlo`). The
    original (unresampled) outcome is marked on both panels, along with the ``goal``/``bust``
    thresholds and probabilities when given.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        sims: Number of simulated paths.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        bust: Optional Max Drawdown threshold (e.g. ``-0.2``), marked on the drawdown panel.
        goal: Optional cumulative-return threshold (e.g. ``1.0``), marked on the return panel.
        confidence: Confidence level, forwarded to :func:`qrt.stats.montecarlo` for the
            reported probabilities. Defaults to ``0.95``.
        seed: Optional random seed for reproducibility.
        block_size: Optional mean block length (in periods) for a stationary block bootstrap,
            preserving autocorrelation/volatility clustering that i.i.d. resampling destroys.
            See the Note on :func:`qrt.stats.montecarlo`. Defaults to ``None`` (i.i.d.).
        periods: Optional simulation horizon in periods, decoupled from ``len(returns)`` so a
            long, multi-regime history can be used as the resampling pool while each simulated
            path only covers a realistic forward horizon (e.g. ``252`` for one trading year).
            See the Note on :func:`qrt.stats.montecarlo`. Defaults to ``None`` (the full length
            of ``returns``).
        title: Figure title. Defaults to ``returns.name``.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    from qrt.stats.core import montecarlo as montecarlo_stats

    result = montecarlo_stats(
        returns,
        sims,
        return_type=return_type,
        bust=bust,
        goal=goal,
        confidence=confidence,
        seed=seed,
        block_size=block_size,
        periods=periods,
    )
    paths: pd.DataFrame = result["paths"]  # type: ignore[assignment]
    terminal = paths.iloc[-1]
    drawdowns = (1.0 + paths).div((1.0 + paths).cummax()).sub(1.0)
    max_drawdowns = drawdowns.min()
    original_terminal = float(terminal["sim_0"])
    original_drawdown = float(max_drawdowns["sim_0"])

    figure = make_subplots(rows=1, cols=2, subplot_titles=("Terminal return", "Max Drawdown"))
    figure.add_histogram(
        x=terminal, nbinsx=40, marker_color=_QUANT_COLORS[0], name="Simulations", showlegend=False, row=1, col=1
    )
    figure.add_histogram(
        x=max_drawdowns, nbinsx=40, marker_color=_QUANT_COLORS[3], name="Simulations", showlegend=False, row=1, col=2
    )

    figure.add_vline(
        x=original_terminal, line={"color": "#111827", "width": 2}, annotation_text="Original", row=1, col=1
    )
    figure.add_vline(
        x=original_drawdown, line={"color": "#111827", "width": 2}, annotation_text="Original", row=1, col=2
    )

    if goal is not None:
        figure.add_vline(
            x=goal, line={"color": _QUANT_COLORS[2], "width": 1.5, "dash": "dash"}, row=1, col=1
        )
        figure.add_vrect(
            x0=goal,
            x1=max(float(terminal.max()), goal),
            fillcolor="rgba(84, 162, 75, 0.12)",
            line_width=0,
            row=1,
            col=1,
        )
    if bust is not None:
        figure.add_vline(
            x=bust, line={"color": _QUANT_COLORS[3], "width": 1.5, "dash": "dash"}, row=1, col=2
        )
        figure.add_vrect(
            x0=min(float(max_drawdowns.min()), bust),
            x1=bust,
            fillcolor="rgba(228, 87, 86, 0.12)",
            line_width=0,
            row=1,
            col=2,
        )

    stat_bits = []
    if result["bust_probability"] is not None:
        stat_bits.append(f"P(bust) {result['bust_probability']:.1%}")
    if result["goal_probability"] is not None:
        stat_bits.append(f"P(goal) {result['goal_probability']:.1%}")

    chart_title = title or (returns.name or "Monte Carlo distribution")
    _base_layout(figure, title=chart_title, subtitle="  ·  ".join(stat_bits) or None, height=height, time_axis=False)
    figure.update_layout(hovermode="closest")
    figure.update_xaxes(title_text="Cumulative return", tickformat=".0%", row=1, col=1)
    figure.update_xaxes(title_text="Max Drawdown", tickformat=".0%", row=1, col=2)
    figure.update_yaxes(title_text="Simulations", row=1, col=1)
    return figure


def trades(
    trades: pd.DataFrame,
    prices: pd.Series | pd.DataFrame,
    *,
    features: pd.DataFrame | None = None,
    title: str | None = None,
    height: int = 520,
) -> Figure:
    """Create an interactive price chart with entry/exit markers for a trade log.

    Renders the price series with one marker per trade entry (triangle up
    for longs, down for shorts) and exit (x, green for winners, red for
    losers), plus a translucent span shading each trade by outcome. Hovering
    a marker shows the trade's reason, return, holding period, and any
    feature-snapshot columns beyond the reserved trades-format set.

    Args:
        trades: Canonical trades-format DataFrame (see :mod:`qrt.data.datasets`).
        prices: Close series (or OHLCV frame with a ``close`` column) with a
            ``DatetimeIndex`` covering the trade span.
        features: Optional datetime-indexed frame of indicator series (e.g.
            moving averages recomputed via :mod:`qrt.feat`) drawn as overlay
            lines on the price axis.
        title: Figure title.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    from qrt.stats.core import TRADE_COLUMNS, _validate_trades

    _validate_trades(trades, ("entry_time", "exit_time", "direction", "entry_price", "exit_price", "return"))
    close = prices["close"] if isinstance(prices, pd.DataFrame) else prices
    snapshots = [column for column in trades.columns if column not in TRADE_COLUMNS]

    figure = go.Figure()
    figure.add_scatter(
        x=close.index, y=close, mode="lines", name=close.name or "Price",
        line={"color": "#9CA3AF", "width": 1.3},
    )
    for index, column in enumerate(features.columns if features is not None else []):
        figure.add_scatter(
            x=features.index, y=features[column], mode="lines", name=str(column),
            line={"color": _QUANT_COLORS[index % len(_QUANT_COLORS)], "width": 1.2},
        )

    wins = trades["return"] > 0
    for start, end, win in zip(trades["entry_time"], trades["exit_time"], wins):
        figure.add_vrect(
            x0=start.isoformat(), x1=end.isoformat(), layer="below", line_width=0,
            fillcolor="#54A24B" if win else "#E45756", opacity=0.10,
        )

    days = ((trades["exit_time"] - trades["entry_time"]) / pd.Timedelta(days=1)).astype(int)
    snapshot_hover = "".join(
        f"<br>{column}: %{{customdata[{i + 4}]:.4g}}" for i, column in enumerate(snapshots)
    )
    # one entry trace per direction so the legend shows the correct arrow
    # for each (a single trace's legend icon would only show one symbol)
    for direction, label, symbol in ((1, "long", "triangle-up"), (-1, "short", "triangle-down")):
        subset = trades[trades["direction"] == direction]
        if subset.empty:
            continue
        subset_days = ((subset["exit_time"] - subset["entry_time"]) / pd.Timedelta(days=1)).astype(int)
        entry_custom = np.column_stack(
            [np.full(len(subset), label), subset.get("entry_reason", ""), subset["return"], subset_days]
            + [subset[column] for column in snapshots]
        )
        figure.add_scatter(
            x=subset["entry_time"], y=subset["entry_price"], mode="markers",
            name=f"Entry ({label})",
            marker={"symbol": symbol, "size": 9, "color": "#374151"},
            customdata=entry_custom,
            hovertemplate=(
                "Entry %{x|%Y-%m-%d} @ %{y:.2f}<br>%{customdata[0]} · %{customdata[1]}"
                + snapshot_hover + "<extra></extra>"
            ),
        )
    figure.add_scatter(
        x=trades["exit_time"], y=trades["exit_price"], mode="markers", name="Exit",
        marker={
            "symbol": "x", "size": 8,
            "color": wins.map({True: "#54A24B", False: "#E45756"}),
        },
        customdata=np.column_stack([trades.get("exit_reason", ""), trades["return"], days]),
        hovertemplate=(
            "Exit %{x|%Y-%m-%d} @ %{y:.2f}<br>%{customdata[0]}"
            "<br>return: %{customdata[1]:.2%} · %{customdata[2]} days<extra></extra>"
        ),
    )

    _base_layout(figure, title=title or "Trades", height=height)
    figure.update_layout(hovermode="closest")
    _set_date_range(figure, close.index)
    figure.update_yaxes(title_text="Price")
    return figure


def mae_mfe(
    trades: pd.DataFrame,
    *,
    title: str | None = None,
    height: int = 430,
) -> Figure:
    """Create an interactive MAE/MFE excursion scatter from a trade log.

    Two panels sharing the trade-return y-axis: max adverse excursion (how
    far each trade went against you -- informs stop placement) and max
    favorable excursion (how much open profit existed -- informs profit
    taking). Dashed identity lines mark the bounds ``return >= MAE`` and
    ``return <= MFE``; exits near the MFE line captured most of their open
    profit, winners far below it round-tripped gains.

    Args:
        trades: Canonical trades-format DataFrame with ``mae``/``mfe`` columns.
        title: Figure title.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.
    """
    from qrt.stats.core import _validate_trades

    _validate_trades(trades, ("entry_time", "exit_time", "direction", "return", "mae", "mfe"))
    wins = trades["return"] > 0
    days = ((trades["exit_time"] - trades["entry_time"]) / pd.Timedelta(days=1)).astype(int)
    custom = np.column_stack([trades["entry_time"].dt.strftime("%Y-%m-%d"), trades.get("exit_reason", ""), days])
    colors = wins.map({True: "#54A24B", False: "#E45756"})

    figure = make_subplots(
        rows=1, cols=2, shared_yaxes=True,
        subplot_titles=("Max Adverse Excursion", "Max Favorable Excursion"),
    )
    for col_index, excursion in ((1, "mae"), (2, "mfe")):
        figure.add_scatter(
            x=trades[excursion], y=trades["return"], mode="markers",
            marker={"color": colors, "size": 7, "opacity": 0.75},
            customdata=custom, showlegend=False,
            hovertemplate=(
                f"{excursion.upper()}: %{{x:.2%}} · return: %{{y:.2%}}"
                "<br>%{customdata[0]} · %{customdata[1]} · %{customdata[2]} days<extra></extra>"
            ),
            row=1, col=col_index,
        )
        bound = trades[excursion].agg(["min", "max"])
        figure.add_scatter(
            x=bound, y=bound, mode="lines", showlegend=False,
            line={"color": "#6B7280", "width": 1, "dash": "dash"},
            hoverinfo="skip", row=1, col=col_index,
        )

    _base_layout(figure, title=title or "Trade excursions", height=height, time_axis=False)
    figure.update_layout(hovermode="closest")
    figure.update_xaxes(tickformat=".0%")
    figure.update_yaxes(tickformat=".0%")
    figure.update_yaxes(title_text="Trade return", row=1, col=1)
    return figure


def trade_distribution(
    trades: pd.DataFrame,
    by: str = "exit_reason",
    *,
    title: str | None = None,
    height: int = 430,
) -> Figure:
    """Create an interactive box plot of per-trade returns grouped by a column.

    Args:
        trades: Canonical trades-format DataFrame (see :mod:`qrt.data.datasets`).
        by: Trades column to group by (e.g. ``"exit_reason"``,
            ``"direction"``, or any feature-snapshot column).
        title: Figure title.
        height: Figure height in pixels.

    Returns:
        A Plotly ``Figure``.

    Raises:
        ValueError: If ``by`` is not a trades column.
    """
    from qrt.stats.core import _validate_trades

    _validate_trades(trades, ("entry_time", "exit_time", "direction", "return"))
    if by not in trades.columns:
        raise ValueError(f"by={by!r} is not a trades column. Available: {list(trades.columns)}")

    figure = go.Figure()
    for index, (value, group) in enumerate(trades.groupby(by, observed=True)):
        figure.add_box(
            y=group["return"], name=str(value),
            boxpoints="all", jitter=0.4, pointpos=0, marker={"size": 4, "opacity": 0.6},
            line={"width": 1.5}, marker_color=_QUANT_COLORS[index % len(_QUANT_COLORS)],
        )
    figure.add_hline(y=0.0, line={"color": "#6B7280", "width": 1, "dash": "dash"})
    _base_layout(figure, title=title or f"Trade returns by {by}", height=height, time_axis=False)
    figure.update_layout(hovermode="closest", showlegend=False)
    figure.update_yaxes(title_text="Trade return", tickformat=".1%")
    figure.update_xaxes(title_text=by)
    return figure


def show(
    figure: Figure,
    name: str | None = None,
    *,
    save_to: str | Path | None = None,
    formats: Iterable[str] = ("png",),
    width: int = 1400,
    height: int = 800,
    scale: int = 2,
) -> None:
    """Display a figure, optionally saving it to `save_to` as PNG (default) and/or self-contained HTML.

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
    if save_to is not None:
        if name is None:
            raise ValueError("name is required when save_to is provided")
        output_dir = Path(save_to)
        output_dir.mkdir(parents=True, exist_ok=True)
        for figure_format in formats:
            if figure_format == "html":
                figure.write_html(output_dir / f"{name}.html", include_plotlyjs=True)
            elif figure_format == "png":
                figure.write_image(output_dir / f"{name}.png", width=width, height=height, scale=scale)
            else:
                raise ValueError(f"Unsupported format: {figure_format!r}. Use 'html' and/or 'png'")
    figure.show()


__all__ = [
    "cumulative_returns",
    "daily_returns",
    "drawdown",
    "eoy_returns",
    "equity",
    "factor_contributions",
    "factor_loadings",
    "line",
    "mae_mfe",
    "metrics_table",
    "montecarlo",
    "montecarlo_distribution",
    "monthly_distribution",
    "monthly_heatmap",
    "noise_test",
    "performance",
    "report",
    "return_quantiles",
    "rolling_beta",
    "rolling_factor_betas",
    "rolling_sharpe",
    "rolling_sortino",
    "rolling_volatility",
    "show",
    "trade_distribution",
    "trades",
    "variance_test",
    "worst_drawdowns",
]
