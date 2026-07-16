"""Statistical analytics for return streams (no plotting dependencies)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from plotly.graph_objects import Figure

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
    beta_series = rolling_beta(strategy, reference, window)
    return (strategy.sub(beta_series.mul(reference)).rolling(window).mean() * periods).rename("Rolling Alpha")


def beta(
    returns: pd.Series,
    benchmark: pd.Series,
    *,
    return_type: ReturnType = "simple",
) -> float:
    """Calculate the market beta of a return stream relative to a benchmark.

    Args:
        returns: Strategy periodic return series.
        benchmark: Benchmark periodic return series, aligned on shared dates.
        return_type: Whether ``returns``/``benchmark`` are ``"simple"`` or
            ``"log"`` returns.

    Returns:
        The beta coefficient (covariance with the benchmark over benchmark variance).
    """
    strategy, reference = _aligned_returns(returns, benchmark, return_type)
    variance = reference.var()
    return float(strategy.cov(reference) / variance) if variance else float("nan")


def alpha(
    returns: pd.Series,
    benchmark: pd.Series,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
) -> float:
    """Calculate the annualized Jensen alpha of a return stream relative to a benchmark.

    Args:
        returns: Strategy periodic return series.
        benchmark: Benchmark periodic return series, aligned on shared dates.
        return_type: Whether ``returns``/``benchmark`` are ``"simple"`` or
            ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.

    Returns:
        Annualized alpha (excess return not explained by benchmark beta exposure).
    """
    strategy, reference = _aligned_returns(returns, benchmark, return_type)
    periods = _periods_per_year(periods_per_year, strategy.index)
    beta_value = beta(strategy, reference, return_type="simple")
    if not np.isfinite(beta_value):
        return float("nan")
    return float((strategy - beta_value * reference).mean() * periods)


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
    beta_value = strategy.cov(reference) / reference.var() if reference.var() else float("nan")
    alpha_value = (strategy - beta_value * reference).mean() * periods if np.isfinite(beta_value) else float("nan")
    tracking_error = active.std(ddof=1) * periods**0.5 if len(active) > 1 else float("nan")
    information_ratio = active.mean() / active.std(ddof=1) * periods**0.5 if tracking_error else float("nan")
    relative_equity = (1.0 + strategy).cumprod().div((1.0 + reference).cumprod())

    return pd.Series(
        {
            "Strategy Total Return": (1.0 + strategy).prod() - 1.0,
            "Benchmark Total Return": (1.0 + reference).prod() - 1.0,
            "Active Return": relative_equity.iloc[-1] - 1.0,
            "Beta": beta_value,
            "Alpha": alpha_value,
            "Correlation": strategy.corr(reference),
            "Tracking Error": tracking_error,
            "Information Ratio": information_ratio,
            "Periods": len(strategy),
        },
        dtype=float,
        name=f"{strategy.name} vs {reference.name}",
    )


class Returns:
    """Bind a return stream (and optional benchmark) for chained stats and plotting.

    Created via :func:`returns`; not intended to be instantiated directly.
    """

    def __init__(
        self,
        data: pd.Series,
        benchmark: pd.Series | None = None,
        *,
        return_type: ReturnType = "simple",
        periods_per_year: int | None = None,
    ) -> None:
        self.returns = _simple_returns(data, return_type)
        self.benchmark = _simple_returns(benchmark, return_type, "Benchmark") if benchmark is not None else None
        self.periods_per_year = periods_per_year

    def _require_benchmark(self) -> pd.Series:
        if self.benchmark is None:
            raise ValueError("This stat requires a benchmark; pass benchmark=... to qrt.stats.returns(...)")
        return self.benchmark

    def performance(self) -> pd.Series:
        """See :func:`performance`."""
        return performance(self.returns, periods_per_year=self.periods_per_year)

    def alpha(self) -> float:
        """See :func:`alpha`."""
        return alpha(self.returns, self._require_benchmark(), periods_per_year=self.periods_per_year)

    def beta(self) -> float:
        """See :func:`beta`."""
        return beta(self.returns, self._require_benchmark())

    def rolling_alpha(self, window: int = 63) -> pd.Series:
        """See :func:`rolling_alpha`."""
        return rolling_alpha(self.returns, self._require_benchmark(), window, periods_per_year=self.periods_per_year)

    def rolling_beta(self, window: int = 63) -> pd.Series:
        """See :func:`rolling_beta`."""
        return rolling_beta(self.returns, self._require_benchmark(), window)

    def rolling_sharpe(self, window: int = 63) -> pd.Series:
        """See :func:`rolling_sharpe`."""
        return rolling_sharpe(self.returns, window, periods_per_year=self.periods_per_year)

    def rolling_volatility(self, window: int = 63) -> pd.Series:
        """See :func:`rolling_volatility`."""
        return rolling_volatility(self.returns, window, periods_per_year=self.periods_per_year)

    def monthly_returns(self) -> pd.DataFrame:
        """See :func:`monthly_returns`."""
        return monthly_returns(self.returns)

    def benchmark_stats(self) -> pd.Series:
        """See :func:`benchmark_stats`."""
        return benchmark_stats(self.returns, self._require_benchmark(), periods_per_year=self.periods_per_year)

    def plot(self, kind: str = "performance", **kwargs: object) -> Figure:
        """Render this return stream with :mod:`qrt.plot`.

        Args:
            kind: One of ``"performance"``/``"tearsheet"``, ``"equity"``,
                ``"drawdown"``, or ``"monthly_heatmap"``.
            **kwargs (Any): Forwarded to the underlying ``qrt.plot`` function.

        Returns:
            A Plotly ``Figure``.
        """
        from qrt import plot as _plot

        dispatch = {
            "performance": _plot.plot,
            "tearsheet": _plot.tearsheet,
            "equity": _plot.equity,
            "drawdown": _plot.drawdown,
            "monthly_heatmap": _plot.monthly_heatmap,
        }
        if kind not in dispatch:
            raise ValueError(f"Unknown plot kind {kind!r}. Use one of {sorted(dispatch)}")
        if kind in ("performance", "tearsheet") and self.benchmark is not None:
            kwargs.setdefault("benchmark", self.benchmark)
        return dispatch[kind](self.returns, **kwargs)


def returns(
    data: pd.Series,
    benchmark: pd.Series | None = None,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
) -> Returns:
    """Bind a return stream (and optional benchmark) for chained stats and plotting.

    Args:
        data: Periodic return series (simple or log, per ``return_type``).
        benchmark: Optional benchmark periodic return series, aligned to
            ``data`` on shared dates. Required for relative stats such as
            ``.alpha()``/``.beta()``.
        return_type: Whether ``data``/``benchmark`` are ``"simple"`` or
            ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.

    Returns:
        A :class:`Returns` object exposing bound stats (``.performance()``,
        ``.alpha()``, ``.beta()``, ``.rolling_beta()``, ...) and ``.plot(kind=...)``.
    """
    return Returns(data, benchmark, return_type=return_type, periods_per_year=periods_per_year)
