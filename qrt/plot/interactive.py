"""Interactive Plotly charts for quantitative research return streams."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from qrt.plot.core import _as_frame
from qrt.stats.core import (
    ReturnType,
    _aligned_returns,
    _periods_per_year,
    _simple_returns,
    monthly_returns,
    performance as performance_stats,
)

if TYPE_CHECKING:
    from plotly.graph_objects import Figure

_QUANT_COLORS = ("#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2", "#B279A2")


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
    _base_layout(figure, title=title, height=height or max(320, 80 * len(table) + 170), time_axis=False)
    figure.update_layout(hovermode="closest")
    figure.update_xaxes(side="top")
    figure.update_yaxes(autorange="reversed", showgrid=False, title_text="")
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
    "drawdown",
    "equity",
    "line",
    "montecarlo",
    "montecarlo_distribution",
    "monthly_heatmap",
    "noise_test",
    "performance",
    "show",
    "variance_test",
]
