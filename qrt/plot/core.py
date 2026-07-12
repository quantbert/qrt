"""Matplotlib plotting primitives with defaults suited to financial time series."""

from __future__ import annotations

from calendar import month_abbr
from collections.abc import Iterable
from fnmatch import fnmatch
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
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


ReturnType = Literal["simple", "log"]


def _simple_returns(
    returns: pd.Series, return_type: ReturnType = "simple", name: str = "returns"
) -> pd.Series:
    """Validate returns and convert log returns to simple returns when needed."""
    if not isinstance(returns, pd.Series):
        raise TypeError("returns must be a pandas Series")
    if not pd.api.types.is_numeric_dtype(returns):
        raise TypeError("returns must contain numeric values")
    if return_type not in ("simple", "log"):
        raise ValueError("return_type must be either 'simple' or 'log'")

    series = returns.astype(float).dropna().rename(returns.name or name)
    if series.empty:
        raise ValueError("returns must contain at least one non-null value")
    if not np.isfinite(series.to_numpy()).all():
        raise ValueError("returns must not contain infinite values")

    simple = np.expm1(series) if return_type == "log" else series
    if (simple < -1.0).any():
        raise ValueError("simple returns must be greater than or equal to -1")
    return simple


def infer_periods_per_year(index: pd.Index) -> int:
    """Infer a conventional annualization frequency from a datetime index.

    Daily and intraday data use 252 trading periods per year. Weekly, monthly,
    quarterly, and yearly data use 52, 12, 4, and 1 periods respectively.
    Non-datetime or single-observation indexes default to 252.
    """
    if not isinstance(index, pd.DatetimeIndex) or len(index) < 2:
        return 252

    spacing = index.to_series().sort_values().diff().dropna().median()
    if pd.isna(spacing) or spacing <= pd.Timedelta(days=2):
        return 252
    if spacing <= pd.Timedelta(days=8):
        return 52
    if spacing <= pd.Timedelta(days=32):
        return 12
    if spacing <= pd.Timedelta(days=100):
        return 4
    return 1


def _periods_per_year(periods_per_year: int | None, index: pd.Index) -> int:
    """Validate an explicit annualization frequency or infer one from the index."""
    if periods_per_year is None:
        return infer_periods_per_year(index)
    if not isinstance(periods_per_year, int) or isinstance(periods_per_year, bool) or periods_per_year <= 0:
        raise ValueError("periods_per_year must be a positive integer or None")
    return periods_per_year


def _aligned_returns(
    returns: pd.Series, benchmark: pd.Series, return_type: ReturnType
) -> tuple[pd.Series, pd.Series]:
    """Convert and align strategy and benchmark returns on their shared dates."""
    strategy = _simple_returns(returns, return_type, "Strategy")
    reference = _simple_returns(benchmark, return_type, "Benchmark")
    aligned = pd.concat([strategy, reference], axis=1, join="inner").dropna()
    if aligned.empty:
        raise ValueError("returns and benchmark must share at least one non-null observation")
    return aligned.iloc[:, 0], aligned.iloc[:, 1]


def _style_axis(ax: Axes, *, percent_y: bool = False) -> None:
    """Apply a lightweight, readable style without changing global Matplotlib settings."""
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25, linewidth=0.8)
    ax.set_axisbelow(True)
    if percent_y:
        ax.yaxis.set_major_formatter("{x:.0%}")


def performance(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
) -> pd.Series:
    """Calculate standard performance statistics for a periodic return stream.

    Annualized metrics use ``periods_per_year`` when supplied; otherwise, a
    conventional frequency is inferred from a datetime index.
    """
    series = _simple_returns(returns, return_type)
    periods = _periods_per_year(periods_per_year, series.index)
    curve = (1.0 + series).cumprod()
    total_return = curve.iloc[-1] - 1.0
    cagr = curve.iloc[-1] ** (periods / len(series)) - 1.0 if curve.iloc[-1] > 0 else -1.0
    volatility = series.std(ddof=1) * periods**0.5 if len(series) > 1 else float("nan")
    sharpe = series.mean() / series.std(ddof=1) * periods**0.5 if volatility and np.isfinite(volatility) else float("nan")
    downside_deviation = np.sqrt(np.mean(np.minimum(series.to_numpy(), 0.0) ** 2)) * periods**0.5
    sortino = series.mean() * periods / downside_deviation if downside_deviation else float("nan")
    max_drawdown = curve.div(curve.cummax()).sub(1.0).min()
    calmar = cagr / abs(max_drawdown) if max_drawdown else float("nan")

    return pd.Series(
        {
            "Total Return": total_return,
            "CAGR": cagr,
            "Volatility": volatility,
            "Sharpe": sharpe,
            "Sortino": sortino,
            "Calmar": calmar,
            "Max Drawdown": max_drawdown,
            "Win Rate": (series > 0).mean(),
            "Periods": len(series),
        },
        dtype=float,
        name=series.name,
    )


def rolling_volatility(
    returns: pd.Series,
    window: int = 63,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
) -> pd.Series:
    """Return annualized rolling volatility for a periodic return stream."""
    series = _simple_returns(returns, return_type)
    if window < 2:
        raise ValueError("window must be at least 2")
    periods = _periods_per_year(periods_per_year, series.index)
    return (series.rolling(window).std(ddof=1) * periods**0.5).rename(f"{series.name} rolling volatility")


def rolling_sharpe(
    returns: pd.Series,
    window: int = 63,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
) -> pd.Series:
    """Return annualized rolling Sharpe ratios using a zero risk-free rate."""
    series = _simple_returns(returns, return_type)
    if window < 2:
        raise ValueError("window must be at least 2")
    periods = _periods_per_year(periods_per_year, series.index)
    return (series.rolling(window).mean().div(series.rolling(window).std(ddof=1)) * periods**0.5).rename(
        f"{series.name} rolling Sharpe"
    )


def rolling_beta(
    returns: pd.Series,
    benchmark: pd.Series,
    window: int = 63,
    *,
    return_type: ReturnType = "simple",
) -> pd.Series:
    """Return rolling beta of strategy returns relative to a benchmark."""
    strategy, reference = _aligned_returns(returns, benchmark, return_type)
    if window < 2:
        raise ValueError("window must be at least 2")
    return strategy.rolling(window).cov(reference).div(reference.rolling(window).var()).rename("Rolling Beta")


def rolling_alpha(
    returns: pd.Series,
    benchmark: pd.Series,
    window: int = 63,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
) -> pd.Series:
    """Return annualized rolling Jensen alpha relative to a benchmark."""
    strategy, reference = _aligned_returns(returns, benchmark, return_type)
    if window < 2:
        raise ValueError("window must be at least 2")
    periods = _periods_per_year(periods_per_year, strategy.index)
    beta = rolling_beta(strategy, reference, window)
    return (strategy.sub(beta.mul(reference)).rolling(window).mean() * periods).rename("Rolling Alpha")


def monthly_returns(
    returns: pd.Series, *, return_type: ReturnType = "simple"
) -> pd.DataFrame:
    """Compound returns by calendar month into a year-by-month table."""
    series = _simple_returns(returns, return_type)
    if not isinstance(series.index, pd.DatetimeIndex):
        raise TypeError("returns must have a DatetimeIndex for monthly aggregation")

    periods = series.index.to_period("M")
    compounded = (1.0 + series).groupby(periods).prod().sub(1.0)
    table = compounded.groupby([compounded.index.year, compounded.index.month]).first().unstack()
    return table.reindex(columns=range(1, 13)).rename_axis(index="Year", columns="Month")


def monthly_heatmap(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    ax: Axes | None = None,
    title: str = "Monthly returns",
    cmap: str = "RdYlGn",
) -> Axes:
    """Plot compounded calendar-month returns as an annotated heatmap."""
    table = monthly_returns(returns, return_type=return_type)
    if ax is None:
        _, ax = plt.subplots(figsize=(12, max(2.8, 0.6 * len(table) + 1.4)), layout="constrained")

    values = table.to_numpy(dtype=float)
    finite_values = values[np.isfinite(values)]
    limit = max(abs(finite_values.min()), abs(finite_values.max())) if len(finite_values) else 0.01
    image = ax.imshow(np.ma.masked_invalid(values), aspect="auto", cmap=cmap, vmin=-limit, vmax=limit)
    ax.set_xticks(range(12), month_abbr[1:])
    ax.set_yticks(range(len(table)), [str(year) for year in table.index])
    ax.set_title(title)
    for row, values_row in enumerate(values):
        for column, value in enumerate(values_row):
            if np.isfinite(value):
                ax.text(column, row, f"{value:.1%}", ha="center", va="center", fontsize=8)
    ax.figure.colorbar(image, ax=ax, label="Return")
    return ax


def benchmark_stats(
    returns: pd.Series,
    benchmark: pd.Series,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
) -> pd.Series:
    """Calculate relative performance, risk, and attribution versus a benchmark."""
    strategy, reference = _aligned_returns(returns, benchmark, return_type)
    periods = _periods_per_year(periods_per_year, strategy.index)
    active = strategy - reference
    beta = strategy.cov(reference) / reference.var() if reference.var() else float("nan")
    alpha = (strategy - beta * reference).mean() * periods if np.isfinite(beta) else float("nan")
    tracking_error = active.std(ddof=1) * periods**0.5 if len(active) > 1 else float("nan")
    information_ratio = active.mean() / active.std(ddof=1) * periods**0.5 if tracking_error else float("nan")
    relative_equity = (1.0 + strategy).cumprod().div((1.0 + reference).cumprod())

    return pd.Series(
        {
            "Strategy Total Return": (1.0 + strategy).prod() - 1.0,
            "Benchmark Total Return": (1.0 + reference).prod() - 1.0,
            "Active Return": relative_equity.iloc[-1] - 1.0,
            "Beta": beta,
            "Alpha": alpha,
            "Correlation": strategy.corr(reference),
            "Tracking Error": tracking_error,
            "Information Ratio": information_ratio,
            "Periods": len(strategy),
        },
        dtype=float,
        name=f"{strategy.name} vs {reference.name}",
    )


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
    return_type: ReturnType = "simple",
    ax: Axes | None = None,
    title: str = "Equity curve",
    label: str | None = None,
    **plot_kwargs: object,
) -> Axes:
    """Plot a compounded equity curve from periodic simple or log returns."""
    series = _simple_returns(returns, return_type)
    curve = (1.0 + series).cumprod()
    ax = col(curve, ax=ax, title=title, ylabel="Growth of $1", label=label or series.name, **plot_kwargs)
    ax.axhline(1.0, color="#6B7280", linewidth=0.8, linestyle="--")
    return ax


def drawdown(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    ax: Axes | None = None,
    title: str = "Drawdown",
    **plot_kwargs: object,
) -> Axes:
    """Plot the underwater curve calculated from periodic simple or log returns."""
    series = _simple_returns(returns, return_type)
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


def plot(
    returns: pd.Series,
    *,
    benchmark: pd.Series | None = None,
    return_type: ReturnType = "simple",
    periods_per_year: int = 252,
    title: str | None = None,
) -> tuple[Figure, tuple[Axes, Axes]]:
    """Create a compact equity-and-drawdown performance chart.

    The optional benchmark is aligned to the returns index before being shown
    on the equity chart. ``return_type`` defaults to ``"simple"``; pass
    ``"log"`` to convert log returns before calculating equity, drawdown, and
    performance statistics. Prices are not accepted.
    """
    series = _simple_returns(returns, return_type)
    figure, (equity_ax, drawdown_ax) = plt.subplots(
        2, 1, figsize=(11, 7), sharex=True, height_ratios=(3, 1), layout="constrained"
    )
    equity(series, ax=equity_ax, title="Equity curve", label=series.name)

    if benchmark is not None:
        benchmark_series = _simple_returns(benchmark, return_type, "Benchmark").reindex(series.index).dropna()
        equity(benchmark_series, ax=equity_ax, title="Equity curve", label=benchmark_series.name, color=_QUANT_COLORS[1])
        equity_ax.legend(frameon=False, loc="lower left")

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
    """Alias for :func:`plot`, retained as the performance-report entry point."""
    return plot(returns, **kwargs)  # type: ignore[arg-type]