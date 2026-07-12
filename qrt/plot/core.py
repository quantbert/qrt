"""Matplotlib plotting primitives with defaults suited to financial time series."""

from __future__ import annotations

from collections.abc import Iterable
from fnmatch import fnmatch

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure

_QUANT_COLORS = ("#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2", "#B279A2")


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


def _returns_series(returns: pd.Series, name: str = "returns") -> pd.Series:
    """Validate and normalize a return series."""
    if not isinstance(returns, pd.Series):
        raise TypeError("returns must be a pandas Series")
    if not pd.api.types.is_numeric_dtype(returns):
        raise TypeError("returns must contain numeric values")
    return returns.astype(float).dropna().rename(returns.name or name)


def _style_axis(ax: Axes, *, percent_y: bool = False) -> None:
    """Apply a lightweight, readable style without changing global Matplotlib settings."""
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25, linewidth=0.8)
    ax.set_axisbelow(True)
    if percent_y:
        ax.yaxis.set_major_formatter("{x:.0%}")


def col(
    data: pd.Series | pd.DataFrame,
    columns: str | Iterable[str] | None = None,
    *,
    ax: Axes | None = None,
    title: str | None = None,
    ylabel: str | None = None,
    **plot_kwargs: object,
) -> Axes:
    """Plot DataFrame columns, optionally selected with shell-style wildcards.

    Args:
        data: Series or DataFrame to plot.
        columns: Column name, wildcard (for example ``"*_log_ret"``), or a
            sequence of names/patterns. Defaults to every column.
        ax: Existing Matplotlib axes. A new figure is created when omitted.
        title: Figure title. Defaults to the plotted column name(s).
        ylabel: Label for the y-axis.
        **plot_kwargs: Additional keyword arguments forwarded to Matplotlib.

    Returns:
        The axes containing the plot.
    """
    frame = _as_frame(data, columns)
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 4.5), layout="constrained")

    kwargs = {"linewidth": 1.5, **plot_kwargs}
    for index, column in enumerate(frame.columns):
        line_kwargs = {"label": str(column), "color": _QUANT_COLORS[index % len(_QUANT_COLORS)], **kwargs}
        ax.plot(frame.index, frame[column], **line_kwargs)

    _style_axis(ax)
    ax.set_title(title or (str(frame.columns[0]) if len(frame.columns) == 1 else "Quantitative research series"))
    if ylabel:
        ax.set_ylabel(ylabel)
    if len(frame.columns) > 1:
        ax.legend(frameon=False)
    return ax


def equity(
    returns: pd.Series,
    *,
    ax: Axes | None = None,
    title: str = "Equity curve",
    label: str | None = None,
    **plot_kwargs: object,
) -> Axes:
    """Plot a compounded equity curve from periodic simple returns."""
    series = _returns_series(returns)
    curve = (1.0 + series).cumprod()
    ax = col(curve, ax=ax, title=title, ylabel="Growth of $1", label=label or series.name, **plot_kwargs)
    ax.axhline(1.0, color="#6B7280", linewidth=0.8, linestyle="--")
    return ax


def drawdown(
    returns: pd.Series,
    *,
    ax: Axes | None = None,
    title: str = "Drawdown",
    **plot_kwargs: object,
) -> Axes:
    """Plot the underwater curve calculated from periodic simple returns."""
    series = _returns_series(returns)
    curve = (1.0 + series).cumprod()
    underwater = curve.div(curve.cummax()).sub(1.0)
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 2.8), layout="constrained")

    kwargs = {"color": "#E45756", "alpha": 0.8, **plot_kwargs}
    ax.fill_between(underwater.index, underwater, 0.0, **kwargs)
    _style_axis(ax, percent_y=True)
    ax.set_title(title)
    ax.set_ylabel("Drawdown")
    return ax


def _performance_stats(returns: pd.Series, periods_per_year: int) -> dict[str, float]:
    curve = (1.0 + returns).cumprod()
    years = len(returns) / periods_per_year
    cagr = curve.iloc[-1] ** (1 / years) - 1 if years > 0 else float("nan")
    volatility = returns.std(ddof=1) * periods_per_year**0.5
    sharpe = returns.mean() / returns.std(ddof=1) * periods_per_year**0.5 if returns.std(ddof=1) else float("nan")
    max_drawdown = curve.div(curve.cummax()).sub(1.0).min()
    return {"CAGR": cagr, "Volatility": volatility, "Sharpe": sharpe, "Max DD": max_drawdown}


def qplot(
    returns: pd.Series,
    *,
    benchmark: pd.Series | None = None,
    periods_per_year: int = 252,
    title: str | None = None,
) -> tuple[Figure, tuple[Axes, Axes]]:
    """Create a compact equity-and-drawdown performance chart.

    The optional benchmark is aligned to the returns index before being shown
    on the equity chart. Return values are simple periodic returns, not prices.
    """
    series = _returns_series(returns)
    figure, (equity_ax, drawdown_ax) = plt.subplots(
        2, 1, figsize=(11, 7), sharex=True, height_ratios=(3, 1), layout="constrained"
    )
    equity(series, ax=equity_ax, title="Equity curve", label=series.name)

    if benchmark is not None:
        benchmark_series = _returns_series(benchmark, "Benchmark").reindex(series.index).dropna()
        equity(benchmark_series, ax=equity_ax, title="Equity curve", label=benchmark_series.name, color=_QUANT_COLORS[1])
        equity_ax.legend(frameon=False)

    equity_ax.set_title("")
    drawdown(series, ax=drawdown_ax)
    stats = _performance_stats(series, periods_per_year)
    stats_text = "   ".join(
        f"{name}: {value:.2%}" if name != "Sharpe" else f"{name}: {value:.2f}" for name, value in stats.items()
    )
    figure.suptitle(title or series.name, fontweight="bold", x=0.06, ha="left")
    figure.text(0.06, 0.93, stats_text, color="#374151")
    return figure, (equity_ax, drawdown_ax)


def tearsheet(returns: pd.Series, **kwargs: object) -> tuple[Figure, tuple[Axes, Axes]]:
    """Alias for :func:`qplot`, retained as the performance-report entry point."""
    return qplot(returns, **kwargs)  # type: ignore[arg-type]