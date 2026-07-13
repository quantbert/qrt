"""Return analytics and Plotly plotting primitives for financial time series."""

from __future__ import annotations

from collections.abc import Iterable
from fnmatch import fnmatch
from typing import TYPE_CHECKING, Literal

import numpy as np
import pandas as pd

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

    Args:
        index: Datetime index whose median spacing is used to infer frequency.

    Returns:
        Periods per year (e.g. 252, 52, 12, 4, or 1).
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


def performance(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
) -> pd.Series:
    """Calculate standard performance statistics for a periodic return stream.

    Annualized metrics use ``periods_per_year`` when supplied; otherwise, a
    conventional frequency is inferred from a datetime index.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.

    Returns:
        Series indexed by metric name: ``Total Return, CAGR, Volatility, Sharpe, Sortino, Calmar, Max Drawdown, Win Rate, Periods``.
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
    """Return annualized rolling volatility for a periodic return stream.

    Args:
        returns: Periodic return series.
        window: Rolling window size, in periods.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.

    Returns:
        Series of annualized rolling volatility.
    """
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
    """Return annualized rolling Sharpe ratios using a zero risk-free rate.

    Args:
        returns: Periodic return series.
        window: Rolling window size, in periods.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.

    Returns:
        Series of annualized rolling Sharpe ratios.
    """
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
    """Return rolling beta of strategy returns relative to a benchmark.

    Args:
        returns: Strategy periodic return series.
        benchmark: Benchmark periodic return series, aligned on shared dates.
        window: Rolling window size, in periods.
        return_type: Whether ``returns``/``benchmark`` are ``"simple"`` or
            ``"log"`` returns.

    Returns:
        Series of rolling beta values.
    """
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
    """Return annualized rolling Jensen alpha relative to a benchmark.

    Args:
        returns: Strategy periodic return series.
        benchmark: Benchmark periodic return series, aligned on shared dates.
        window: Rolling window size, in periods.
        return_type: Whether ``returns``/``benchmark`` are ``"simple"`` or
            ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.

    Returns:
        Series of annualized rolling Jensen alpha.
    """
    strategy, reference = _aligned_returns(returns, benchmark, return_type)
    if window < 2:
        raise ValueError("window must be at least 2")
    periods = _periods_per_year(periods_per_year, strategy.index)
    beta = rolling_beta(strategy, reference, window)
    return (strategy.sub(beta.mul(reference)).rolling(window).mean() * periods).rename("Rolling Alpha")


def monthly_returns(
    returns: pd.Series, *, return_type: ReturnType = "simple"
) -> pd.DataFrame:
    """Compound returns by calendar month into a year-by-month table.

    Args:
        returns: Periodic return series with a ``DatetimeIndex``.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        DataFrame indexed by year with one column per calendar month (1-12).
    """
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


def benchmark_stats(
    returns: pd.Series,
    benchmark: pd.Series,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
) -> pd.Series:
    """Calculate relative performance, risk, and attribution versus a benchmark.

    Args:
        returns: Strategy periodic return series.
        benchmark: Benchmark periodic return series, aligned on shared dates.
        return_type: Whether ``returns``/``benchmark`` are ``"simple"`` or
            ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.

    Returns:
        Series indexed by metric name: ``Strategy Total Return, Benchmark Total Return, Active Return, Beta, Alpha, Correlation, Tracking Error, Information Ratio, Periods``.
    """
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