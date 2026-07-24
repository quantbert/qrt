"""Statistical analytics for return streams (no plotting dependencies)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.stats import t as t_dist

from qrt.stats._returns import ReturnType, _simple_returns
from qrt.stats.risk import historical_expected_shortfall, historical_value_at_risk

if TYPE_CHECKING:
    from plotly.graph_objects import Figure


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


def _excess_returns(series: pd.Series, rf: float, periods: int) -> pd.Series:
    """Subtract a deannualized risk-free rate from each period's return.

    ``rf`` is an annualized rate; it is converted to a per-period rate
    assuming ``periods`` compounding periods per year (``(1 + rf) ** (1 /
    periods) - 1``) before being subtracted, matching common excess-return
    conventions (e.g. [quantstats](https://github.com/ranaroussi/quantstats)).
    A zero ``rf`` (the default) returns ``series`` unchanged.
    """
    if rf == 0:
        return series
    rf_per_period = (1.0 + rf) ** (1.0 / periods) - 1.0
    return series - rf_per_period


def _cagr(excess: pd.Series, periods: int) -> float:
    """Compound a (possibly excess-adjusted) return series into an annualized growth rate."""
    curve = (1.0 + excess).cumprod()
    return curve.iloc[-1] ** (periods / len(excess)) - 1.0 if curve.iloc[-1] > 0 else -1.0


def performance(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
    rf: float = 0.0,
    smart: bool = False,
) -> pd.Series:
    """Calculate standard performance statistics for a periodic return stream.

    Annualized metrics use ``periods_per_year`` when supplied; otherwise, a
    conventional frequency is inferred from a datetime index. ``rf`` (an
    annualized risk-free rate) is deannualized to match ``periods`` and
    subtracted from returns before computing CAGR, Sharpe, and Sortino (and,
    through CAGR, Calmar); Total Return, Volatility, Max Drawdown, and Win
    Rate always use raw returns.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.
        rf: Annualized risk-free rate, subtracted (after deannualizing) from
            returns before computing excess-return ratios. Defaults to ``0.0``.
        smart: Whether to penalize Sharpe/Sortino for return autocorrelation,
            see :func:`sharpe`/:func:`sortino`. Defaults to ``False``.

    Returns:
        Series indexed by metric name:

        - ``Total Return``: Simple compounded return over the full period.
        - ``CAGR``: [Compound Annual Growth Rate](https://en.wikipedia.org/wiki/Compound_annual_growth_rate)
                — the constant annual rate of return that would produce the same total growth.
        - ``Volatility``: [Volatility](https://en.wikipedia.org/wiki/Volatility_(finance)) —
                annualized standard deviation of returns, the most common measure of risk.
        - ``Sharpe``: [Sharpe ratio](https://en.wikipedia.org/wiki/Sharpe_ratio) — annualized
                excess return per unit of volatility, i.e. return earned per unit of total risk taken.
        - ``Sortino``: [Sortino ratio](https://en.wikipedia.org/wiki/Sortino_ratio) — like Sharpe,
                but only penalizes downside volatility, since investors rarely mind upside swings.
        - ``Calmar``: [Calmar ratio](https://en.wikipedia.org/wiki/Calmar_ratio) — CAGR divided by
                the absolute Max Drawdown, i.e. return per unit of worst-case pain endured.
        - ``Max Drawdown``: [Drawdown](https://en.wikipedia.org/wiki/Drawdown_(economics)) —
                largest peak-to-trough decline in cumulative value over the period.
        - ``Win Rate``: Share of non-zero-return periods that were positive
                (periods with exactly zero return are excluded from both the count of wins and the total).
        - ``Periods``: Number of return observations used.
    """
    series = _simple_returns(returns, return_type)
    periods = _periods_per_year(periods_per_year, series.index)
    excess = _excess_returns(series, rf, periods)
    curve = (1.0 + series).cumprod()
    total_return = curve.iloc[-1] - 1.0
    cagr = _cagr(excess, periods)
    volatility = series.std(ddof=1) * periods**0.5 if len(series) > 1 else float("nan")
    sharpe_value = sharpe(series, periods_per_year=periods, rf=rf, smart=smart)
    sortino_value = sortino(series, periods_per_year=periods, rf=rf, smart=smart)
    # cummax() alone would miss a drawdown on the very first period, since it treats
    # curve[0] as the peak; clip to the implicit starting capital of 1.0 to catch it.
    max_drawdown = curve.div(curve.cummax().clip(lower=1.0)).sub(1.0).min()
    calmar = cagr / abs(max_drawdown) if max_drawdown else float("nan")
    non_zero = series[series != 0]
    win_rate = (non_zero > 0).mean() if len(non_zero) else float("nan")

    return pd.Series(
        {
            "Total Return": total_return,
            "CAGR": cagr,
            "Volatility": volatility,
            "Sharpe": sharpe_value,
            "Sortino": sortino_value,
            "Calmar": calmar,
            "Max Drawdown": max_drawdown,
            "Win Rate": win_rate,
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

    [Volatility](https://en.wikipedia.org/wiki/Volatility_(finance)) is the standard deviation of
    returns — the most common measure of risk. Unlike Sortino-style measures, it penalizes upside
    and downside swings equally.

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
    rf: float = 0.0,
) -> pd.Series:
    """Return annualized rolling Sharpe ratios over a moving window.

    The [Sharpe ratio](https://en.wikipedia.org/wiki/Sharpe_ratio) is the annualized mean excess
    return divided by the annualized volatility of returns — return earned per unit of total risk
    taken.

    Args:
        returns: Periodic return series.
        window: Rolling window size, in periods.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.
        rf: Annualized risk-free rate, subtracted (after deannualizing) from
            returns before computing the ratio. Defaults to ``0.0``.

    Returns:
        Series of annualized rolling Sharpe ratios.
    """
    series = _simple_returns(returns, return_type)
    if window < 2:
        raise ValueError("window must be at least 2")
    periods = _periods_per_year(periods_per_year, series.index)
    excess = _excess_returns(series, rf, periods)
    return (excess.rolling(window).mean().div(excess.rolling(window).std(ddof=1)) * periods**0.5).rename(
        f"{series.name} rolling Sharpe"
    )


def rolling_sortino(
    returns: pd.Series,
    window: int = 63,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
    rf: float = 0.0,
) -> pd.Series:
    """Return annualized rolling Sortino ratios over a moving window.

    The [Sortino ratio](https://en.wikipedia.org/wiki/Sortino_ratio) is like the Sharpe ratio, but
    only penalizes downside volatility, since investors rarely mind upside swings.

    Args:
        returns: Periodic return series.
        window: Rolling window size, in periods.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.
        rf: Annualized risk-free rate, subtracted (after deannualizing) from
            returns before computing the ratio. Defaults to ``0.0``.

    Returns:
        Series of annualized rolling Sortino ratios.
    """
    series = _simple_returns(returns, return_type)
    if window < 2:
        raise ValueError("window must be at least 2")
    periods = _periods_per_year(periods_per_year, series.index)
    excess = _excess_returns(series, rf, periods)
    downside_deviation = excess.rolling(window).apply(
        lambda values: np.sqrt(np.mean(np.minimum(values, 0.0) ** 2)), raw=True
    )
    return (excess.rolling(window).mean().div(downside_deviation) * periods**0.5).rename(
        f"{series.name} rolling Sortino"
    )


def rolling_beta(
    returns: pd.Series,
    benchmark: pd.Series,
    window: int = 63,
    *,
    return_type: ReturnType = "simple",
) -> pd.Series:
    """Return rolling beta of strategy returns relative to a benchmark.

    [Beta](https://en.wikipedia.org/wiki/Beta_(finance)) measures sensitivity to benchmark (market)
    movements: the covariance of strategy and benchmark returns divided by the benchmark's
    variance. A beta of 1 tracks the benchmark 1:1; above 1 amplifies its moves; below 1 dampens
    them. See also the
    [Capital Asset Pricing Model](https://en.wikipedia.org/wiki/Capital_asset_pricing_model), which
    uses beta to model expected return as a function of systematic risk.

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

    [Jensen's alpha](https://en.wikipedia.org/wiki/Jensen%27s_alpha) is the annualized return left
    over after accounting for the return explained by beta exposure to the benchmark — the excess
    return generated (or lost) beyond what market risk alone would predict.

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


# ---------------------------------------------------------------------------
# Multi-factor regression (e.g. Fama-French three/five-factor models)
# ---------------------------------------------------------------------------

CovarianceType = Literal["nonrobust", "HC3"]


def _factor_design_matrix(
    returns: pd.Series,
    factors: pd.DataFrame,
    *,
    return_type: ReturnType,
    rf: str | pd.Series | None,
) -> tuple[pd.Series, pd.DataFrame]:
    """Align a return stream with factor returns and build the excess-return regression inputs.

    Inner-joins ``returns`` with every column of ``factors`` on shared dates and drops any
    row with a missing value (never forward-filled). Unless ``rf`` is ``None`` (meaning
    ``returns`` is already excess of the risk-free rate), a per-period risk-free rate is
    subtracted from ``returns`` to form the regression's dependent variable: ``rf`` either
    names a column already present in ``factors`` (removed from the regressors -- e.g. Ken
    French's own ``"RF"`` column, so it isn't also fit as a factor) or is a separate periodic
    risk-free return series aligned like ``factors``.
    """
    if not isinstance(factors, pd.DataFrame) or factors.empty:
        raise TypeError("factors must be a non-empty pandas DataFrame of factor return columns")
    strategy = _simple_returns(returns, return_type, "Strategy")
    if not strategy.index.is_unique or not factors.index.is_unique:
        raise ValueError("returns and factors must not contain duplicate dates")
    # Concat under a private sentinel name (not `strategy.name`) so a strategy series that
    # happens to share a name with one of the factor columns (e.g. "RF") doesn't collide.
    # sort_index() guarantees chronological order, which the rolling window and cumulative
    # contributions depend on.
    frame = pd.concat([strategy.rename("__strategy__"), factors], axis=1, join="inner").dropna().sort_index()
    if frame.empty:
        raise ValueError("returns and factors must share at least one non-null observation")

    rf_series: pd.Series | None = None
    factor_columns = list(factors.columns)
    if isinstance(rf, str):
        if rf not in factor_columns:
            raise ValueError(f"rf={rf!r} is not a column of factors. Available: {factor_columns}")
        rf_series = frame[rf]
        factor_columns.remove(rf)
    elif isinstance(rf, pd.Series):
        rf_series = rf.reindex(frame.index)
        if rf_series.isna().any():
            raise ValueError("rf must cover every aligned returns/factors date")
    elif rf is not None:
        raise TypeError("rf must be a column name (str), a pandas Series, or None")

    if not factor_columns:
        raise ValueError("factors must contain at least one factor column besides rf")
    excess = (frame["__strategy__"] - rf_series) if rf_series is not None else frame["__strategy__"]
    return excess.rename(strategy.name), frame[factor_columns]


def _ols_fit(y: np.ndarray, design: np.ndarray, covariance: CovarianceType) -> dict[str, object]:
    """Fit OLS by least squares and compute coefficient covariance for inference.

    ``design`` is the full design matrix, including a leading constant column for the
    intercept (alpha). Uses ``numpy.linalg`` directly rather than forming an explicit
    matrix inverse of ``design`` itself (only the small ``k x k`` ``(X'X)^-1`` is inverted).
    """
    n, k = design.shape
    if n <= k:
        raise ValueError(f"Need more observations ({n}) than regressors+intercept ({k}) to fit the regression")
    xtx_inv = np.linalg.inv(design.T @ design)
    coefficients = xtx_inv @ design.T @ y
    residuals = y - design @ coefficients
    dof = n - k
    rss = float(residuals @ residuals)
    sigma2 = rss / dof

    if covariance == "nonrobust":
        cov_matrix = sigma2 * xtx_inv
    elif covariance == "HC3":
        # White's HC3 estimator: leverage-corrected squared residuals, robust to
        # heteroskedasticity without assuming a particular error variance structure.
        hat_diag = np.einsum("ij,jk,ik->i", design, xtx_inv, design)
        leverage = np.clip(1.0 - hat_diag, 1e-12, None)
        meat = design.T @ (design * (residuals**2 / leverage**2)[:, None])
        cov_matrix = xtx_inv @ meat @ xtx_inv
    else:
        raise ValueError("covariance must be one of 'nonrobust', 'HC3'")

    tss = float(((y - y.mean()) ** 2).sum())
    r_squared = 1.0 - rss / tss if tss else float("nan")
    n_factors = k - 1
    adj_r_squared = 1.0 - (1.0 - r_squared) * (n - 1) / dof if dof > n_factors and np.isfinite(r_squared) else float("nan")
    return {
        "coefficients": coefficients,
        "std_errors": np.sqrt(np.diag(cov_matrix)),
        "residuals": residuals,
        "residual_std": sigma2**0.5,
        "dof": dof,
        "r_squared": r_squared,
        "adj_r_squared": adj_r_squared,
    }


def factor_regression(
    returns: pd.Series,
    factors: pd.DataFrame,
    *,
    return_type: ReturnType = "simple",
    rf: str | pd.Series | None = "RF",
    covariance: CovarianceType = "nonrobust",
    confidence_level: float = 0.95,
) -> pd.DataFrame:
    """Fit a full-period multi-factor OLS regression (e.g. the Fama-French five-factor model).

    Decomposes ``returns``' excess return into a constant (alpha) plus a linear exposure
    (beta) to each column of ``factors``:
    ``R - Rf = alpha + beta_1 * factor_1 + ... + beta_k * factor_k + residual``. This is a
    *return-attribution* regression, not a forecasting model -- it explains what already
    happened, using every observation in the sample. See
    [Fama-French three/five-factor model](https://en.wikipedia.org/wiki/Fama%E2%80%93French_three-factor_model)
    and the [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)
    for the standard ``Mkt-RF``/``SMB``/``HML``/``RMW``/``CMA``/``RF`` factor set (any
    factor set works, not only the Fama-French five). For time-varying exposures, see
    :func:`rolling_factor_regression`.

    Args:
        returns: Strategy periodic return series.
        factors: DataFrame of periodic factor return columns (e.g. ``Mkt-RF``, ``SMB``,
            ``HML``, ``RMW``, ``CMA``, and optionally ``RF``), aligned to ``returns`` on
            shared dates. Must be in the same decimal-return units as ``returns``.
        return_type: Whether ``returns`` is ``"simple"`` or ``"log"`` returns.
        rf: Risk-free rate used to convert ``returns`` into the regression's excess-return
            target. Either a column name already present in ``factors`` (removed from the
            regressors, e.g. Ken French's ``"RF"``) or a separate periodic risk-free return
            series aligned like ``factors``. Pass ``None`` if ``returns`` is already an
            excess return.
        covariance: Standard-error estimator: ``"nonrobust"`` (classic OLS, default) or
            ``"HC3"`` (heteroskedasticity-robust). Coefficients are identical either way;
            only standard errors, t-statistics, p-values, and confidence intervals differ.
        confidence_level: Confidence level for ``CI Lower``/``CI Upper``. Defaults to ``0.95``.

    Returns:
        DataFrame indexed by ``"Alpha"`` followed by each factor column (in ``factors``'
        order, excluding ``rf`` when it names a column), with columns ``Coefficient``,
        ``Std Error``, ``t-Statistic``, ``p-Value``, ``CI Lower``, ``CI Upper``. See
        :func:`factor_regression_stats` for regression-level diagnostics (R², annualized
        alpha, residual volatility) and :func:`factor_contributions` for the per-period
        return attribution this fit implies.
    """
    excess, design_frame = _factor_design_matrix(returns, factors, return_type=return_type, rf=rf)
    design = np.column_stack([np.ones(len(design_frame)), design_frame.to_numpy(dtype=float)])
    fit = _ols_fit(excess.to_numpy(dtype=float), design, covariance)
    coefficients, std_errors = fit["coefficients"], fit["std_errors"]

    t_stats = coefficients / std_errors
    p_values = 2.0 * t_dist.sf(np.abs(t_stats), fit["dof"])
    margin = t_dist.ppf(0.5 + confidence_level / 2.0, fit["dof"]) * std_errors
    return pd.DataFrame(
        {
            "Coefficient": coefficients,
            "Std Error": std_errors,
            "t-Statistic": t_stats,
            "p-Value": p_values,
            "CI Lower": coefficients - margin,
            "CI Upper": coefficients + margin,
        },
        index=["Alpha", *design_frame.columns],
    )


def factor_regression_stats(
    returns: pd.Series,
    factors: pd.DataFrame,
    *,
    return_type: ReturnType = "simple",
    rf: str | pd.Series | None = "RF",
    covariance: CovarianceType = "nonrobust",
    periods_per_year: int | None = None,
) -> pd.Series:
    """Calculate regression-level diagnostics for a full-period multi-factor OLS fit.

    Companion to :func:`factor_regression` (which returns the per-factor coefficient
    table); this returns the fit's overall explanatory power and alpha, annualized.

    Args:
        returns: Strategy periodic return series.
        factors: DataFrame of periodic factor return columns, aligned to ``returns``.
        return_type: Whether ``returns`` is ``"simple"`` or ``"log"`` returns.
        rf: See :func:`factor_regression`.
        covariance: See :func:`factor_regression` (only affects ``Alpha``'s
            statistical significance, not shown here -- see :func:`factor_regression`
            for alpha's standard error/t-statistic/p-value).
        periods_per_year: Annualization frequency. Inferred from the index when not given.

    Returns:
        Series indexed by metric name:

        - ``Alpha``: Per-period (e.g. daily) intercept.
        - ``Alpha (ann.)``: Simple annualization (``periods_per_year * Alpha``); prefer this
                over compounding a regression intercept, which implies more economic precision
                than is justified.
        - ``R²``: Fraction of excess-return variance explained by the factors.
        - ``Adj. R²``: R² penalized for the number of factors, comparable across models
                with a different factor count.
        - ``Residual Volatility``: Annualized standard deviation of the fit's residuals --
                variation left unexplained by the factors.
        - ``Periods``: Number of aligned observations used.
    """
    excess, design_frame = _factor_design_matrix(returns, factors, return_type=return_type, rf=rf)
    periods = _periods_per_year(periods_per_year, excess.index)
    design = np.column_stack([np.ones(len(design_frame)), design_frame.to_numpy(dtype=float)])
    fit = _ols_fit(excess.to_numpy(dtype=float), design, covariance)
    alpha_value = float(fit["coefficients"][0])

    return pd.Series(
        {
            "Alpha": alpha_value,
            "Alpha (ann.)": alpha_value * periods,
            "R²": fit["r_squared"],
            "Adj. R²": fit["adj_r_squared"],
            "Residual Volatility": fit["residual_std"] * periods**0.5,
            "Periods": float(len(excess)),
        },
        name=excess.name,
    )


def rolling_factor_regression(
    returns: pd.Series,
    factors: pd.DataFrame,
    window: int = 63,
    *,
    return_type: ReturnType = "simple",
    rf: str | pd.Series | None = "RF",
    min_observations: int | None = None,
) -> pd.DataFrame:
    """Calculate rolling multi-factor OLS betas over a moving window.

    Refits :func:`factor_regression`'s OLS on each trailing ``window`` of aligned
    observations, e.g. the rolling Fama-French five-factor betas that reveal
    time-varying exposure a single full-period fit cannot. Following
    [``statsmodels.regression.rolling.RollingOLS``](https://www.statsmodels.org/stable/examples/notebooks/generated/rolling_ls.html)'s
    convention, each window's estimate is stored at the date of its *last*
    observation, so the window is a trailing observation window (not a calendar-day
    window) -- with daily data, ``window=63`` is roughly 3 trading months.

    Args:
        returns: Strategy periodic return series.
        factors: DataFrame of periodic factor return columns, aligned to ``returns``.
        window: Trailing window size, in periods. Defaults to ``63``.
        return_type: Whether ``returns`` is ``"simple"`` or ``"log"`` returns.
        rf: See :func:`factor_regression`.
        min_observations: Minimum aligned observations required before the first
            (noisier, shorter-window) estimate is produced. Defaults to ``window``
            (a full window); every estimate still reports its actual observation
            count in ``N Obs``.

    Returns:
        DataFrame indexed like the aligned returns/factors data, with columns
        ``Alpha``, one per factor (in ``factors``' order), ``R²``, and ``N Obs``.
        Rows before the first ``min_observations`` aligned dates are ``NaN``
        (there is no complete window yet).
    """
    excess, design_frame = _factor_design_matrix(returns, factors, return_type=return_type, rf=rf)
    if window < 2:
        raise ValueError("window must be at least 2")
    min_obs = window if min_observations is None else min_observations
    n_regressors = design_frame.shape[1] + 1
    if min_obs <= n_regressors:
        raise ValueError(f"min_observations ({min_obs}) must exceed the number of regressors+intercept ({n_regressors})")

    y = excess.to_numpy(dtype=float)
    x = np.column_stack([np.ones(len(design_frame)), design_frame.to_numpy(dtype=float)])
    columns = ["Alpha", *design_frame.columns, "R²", "N Obs"]
    records = np.full((len(excess), len(columns)), np.nan)
    for end in range(min_obs - 1, len(excess)):
        start = max(0, end - window + 1)
        fit = _ols_fit(y[start : end + 1], x[start : end + 1], "nonrobust")
        records[end, : len(columns) - 2] = fit["coefficients"]
        records[end, -2] = fit["r_squared"]
        records[end, -1] = end - start + 1

    return pd.DataFrame(records, index=excess.index, columns=columns)


def factor_contributions(
    returns: pd.Series,
    factors: pd.DataFrame,
    *,
    return_type: ReturnType = "simple",
    rf: str | pd.Series | None = "RF",
    covariance: CovarianceType = "nonrobust",
) -> pd.DataFrame:
    """Decompose each period's excess return into per-factor contributions from a static fit.

    A factor *loading* (:func:`factor_regression`) answers "how sensitive is the strategy
    to this factor?"; a factor *contribution* answers "how much return did that exposure
    generate?". Fits :func:`factor_regression` once over the full period, then attributes
    every period's excess return to ``Alpha`` (the fitted intercept), one column per factor
    (``coefficient * factor return``), and ``Residual`` (left unexplained). Columns sum,
    period by period, to the excess return (``returns`` minus ``rf``).

    Note:
        Cumulative *arithmetic* sums of these columns reconstruct the cumulative excess
        return exactly; compounding each column separately (e.g. ``(1 + contribution).cumprod()``)
        would not, since return compounding creates cross-factor interaction terms. Use
        arithmetic cumulative sums for additive attribution (see :func:`qrt.plot.factor_contributions`).

    Args:
        returns: Strategy periodic return series.
        factors: DataFrame of periodic factor return columns, aligned to ``returns``.
        return_type: Whether ``returns`` is ``"simple"`` or ``"log"`` returns.
        rf: See :func:`factor_regression`.
        covariance: See :func:`factor_regression` (only affects standard errors, not the
            contributions themselves, which depend only on the fitted coefficients).

    Returns:
        DataFrame indexed like the aligned returns/factors data, with columns ``Alpha``,
        one per factor (in ``factors``' order), and ``Residual``.
    """
    excess, design_frame = _factor_design_matrix(returns, factors, return_type=return_type, rf=rf)
    loadings = factor_regression(returns, factors, return_type=return_type, rf=rf, covariance=covariance)["Coefficient"]

    contributions = design_frame.mul(loadings.drop("Alpha"), axis=1)
    contributions.insert(0, "Alpha", loadings["Alpha"])
    contributions["Residual"] = excess - contributions.sum(axis=1)
    return contributions


def beta(
    returns: pd.Series,
    benchmark: pd.Series,
    *,
    return_type: ReturnType = "simple",
) -> float:
    """Calculate the market beta of a return stream relative to a benchmark.

    [Beta](https://en.wikipedia.org/wiki/Beta_(finance)) is the covariance of strategy and
    benchmark returns divided by the benchmark's variance — a measure of sensitivity to benchmark
    (market) movements, i.e. systematic risk.

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

    [Jensen's alpha](https://en.wikipedia.org/wiki/Jensen%27s_alpha) is the annualized return left
    over after accounting for the return explained by beta exposure to the benchmark — the excess
    return generated (or lost) beyond what market risk alone would predict.

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
    returns: pd.Series, *, return_type: ReturnType = "simple", eoy: bool = True
) -> pd.DataFrame:
    """Compound returns by calendar month into a year-by-month table.

    Useful for spotting seasonal patterns and feeding a monthly-returns
    heatmap (see :func:`qrt.plot.monthly_heatmap`).

    Args:
        returns: Periodic return series with a ``DatetimeIndex``.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        eoy: Whether to append an ``EOY`` (end-of-year) column with each
            year's compounded total return. Defaults to ``True``.

    Returns:
        DataFrame indexed by year with one column per calendar month (1-12),
        plus an ``EOY`` column when ``eoy=True``.
    """
    series = _simple_returns(returns, return_type)
    if not isinstance(series.index, pd.DatetimeIndex):
        raise TypeError("returns must have a DatetimeIndex for monthly aggregation")

    periods = series.index.to_period("M")
    compounded = (1.0 + series).groupby(periods).prod().sub(1.0)
    table = compounded.groupby([compounded.index.year, compounded.index.month]).first().unstack()
    table = table.reindex(columns=range(1, 13)).rename_axis(index="Year", columns="Month")
    if eoy:
        table["EOY"] = (1.0 + series).groupby(series.index.year).prod().sub(1.0)
    return table


_AGGREGATE_RESAMPLE_RULES: dict[str, str] = {"W": "W-MON", "M": "ME", "Q": "QE", "Y": "YE"}


def aggregate_returns(
    returns: pd.Series, period: Literal["W", "M", "Q", "Y"], *, return_type: ReturnType = "simple"
) -> pd.Series:
    """Compound a return series into coarser calendar periods.

    Args:
        returns: Periodic return series with a ``DatetimeIndex``.
        period: Target period: ``"W"`` (weekly), ``"M"`` (monthly), ``"Q"`` (quarterly), or
            ``"Y"`` (yearly).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Series of compounded returns, one value per ``period``, indexed by period end date.
    """
    series = _simple_returns(returns, return_type)
    if not isinstance(series.index, pd.DatetimeIndex):
        raise TypeError("returns must have a DatetimeIndex for period aggregation")
    if period not in _AGGREGATE_RESAMPLE_RULES:
        raise ValueError(f"period must be one of {sorted(_AGGREGATE_RESAMPLE_RULES)}")
    compounded = (1.0 + series).resample(_AGGREGATE_RESAMPLE_RULES[period]).prod().sub(1.0)
    return compounded.rename(series.name)


def period_returns(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
) -> pd.Series:
    """Compound returns over standard trailing and calendar windows (MTD, 3M, ..., all-time).

    Windows shorter than one year report the plain compounded return; multi-year
    windows report the annualized (CAGR) rate. Windows extending before the first
    observation use whatever data is available.

    Args:
        returns: Periodic return series with a ``DatetimeIndex``.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency for the multi-year windows.
            Inferred from the index when not given.

    Returns:
        Series indexed by window label: ``MTD``, ``3M``, ``6M``, ``YTD``, ``1Y``,
        ``3Y (ann.)``, ``5Y (ann.)``, ``10Y (ann.)``, and ``All-time (ann.)``.
    """
    series = _simple_returns(returns, return_type)
    if not isinstance(series.index, pd.DatetimeIndex):
        raise TypeError("returns must have a DatetimeIndex for period returns")
    periods = _periods_per_year(periods_per_year, series.index)
    end = series.index[-1]

    def compound(window: pd.Series) -> float:
        return float((1.0 + window).prod() - 1.0) if len(window) else float("nan")

    def annualized(window: pd.Series) -> float:
        return float(_cagr(window, periods)) if len(window) else float("nan")

    return pd.Series(
        {
            "MTD": compound(series.loc[end.replace(day=1) :]),
            "3M": compound(series.loc[end - pd.DateOffset(months=3) :]),
            "6M": compound(series.loc[end - pd.DateOffset(months=6) :]),
            "YTD": compound(series.loc[end.replace(month=1, day=1) :]),
            "1Y": compound(series.loc[end - pd.DateOffset(years=1) :]),
            "3Y (ann.)": annualized(series.loc[end - pd.DateOffset(years=3) :]),
            "5Y (ann.)": annualized(series.loc[end - pd.DateOffset(years=5) :]),
            "10Y (ann.)": annualized(series.loc[end - pd.DateOffset(years=10) :]),
            "All-time (ann.)": annualized(series),
        },
        dtype=float,
        name=series.name,
    )


def to_prices(returns: pd.Series, *, return_type: ReturnType = "simple", base: float = 1.0) -> pd.Series:
    """Convert a return series into a cumulative price/equity curve.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        base: Starting value of the curve. Defaults to ``1.0``.

    Returns:
        Cumulative price series starting at ``base``, same index as ``returns``.
    """
    series = _simple_returns(returns, return_type)
    return (base * (1.0 + series).cumprod()).rename(f"{series.name} price")


def rebase(prices: pd.Series, base: float = 100.0) -> pd.Series:
    """Rescale a price series to a common starting value.

    Useful for plotting or comparing price series that start on different scales
    (e.g. a strategy's equity curve against a benchmark index).

    Args:
        prices: Price series. Must contain at least one non-null, non-zero value.
        base: Starting value after rebasing. Defaults to ``100.0``.

    Returns:
        Rebased price series, same index as ``prices``.
    """
    if not isinstance(prices, pd.Series):
        raise TypeError("prices must be a pandas Series")
    clean = prices.dropna()
    if clean.empty:
        raise ValueError("prices must contain at least one non-null value")
    if clean.iloc[0] == 0:
        raise ValueError("prices must not start at zero")
    return (prices / clean.iloc[0] * base).rename(prices.name)


def make_portfolio(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    start_balance: float = 100_000.0,
    mode: Literal["compound", "linear"] = "compound",
) -> pd.Series:
    """Turn a return series into a portfolio equity curve.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        start_balance: Starting portfolio balance. Defaults to ``100,000``.
        mode: ``"compound"`` (default) reinvests gains/losses each period (equivalent to
            :func:`to_prices`, rebased to ``start_balance``); ``"linear"`` applies each
            period's return to the original ``start_balance`` only, without reinvestment.

    Returns:
        Portfolio balance series, same index as ``returns``.
    """
    series = _simple_returns(returns, return_type)
    if mode == "compound":
        return to_prices(series, base=start_balance).rename(f"{series.name} portfolio")
    if mode == "linear":
        return (start_balance * (1.0 + series.cumsum())).rename(f"{series.name} portfolio")
    raise ValueError("mode must be either 'compound' or 'linear'")


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
        Series indexed by metric name:

        - ``Strategy Total Return`` / ``Benchmark Total Return``: Simple
                compounded returns over the full period.
        - ``Active Return``: Geometric excess growth of the strategy over the
                benchmark (final value of the strategy/benchmark equity ratio, minus 1).
        - ``Beta``: [Beta](https://en.wikipedia.org/wiki/Beta_(finance)) — sensitivity to
                benchmark movements.
        - ``Alpha``: [Jensen's alpha](https://en.wikipedia.org/wiki/Jensen%27s_alpha) —
                annualized excess return not explained by beta exposure.
        - ``Correlation``: [Correlation](https://en.wikipedia.org/wiki/Correlation) — Pearson
                correlation between strategy and benchmark returns.
        - ``Tracking Error``: [Tracking error](https://en.wikipedia.org/wiki/Tracking_error) —
                annualized standard deviation of active returns (strategy minus benchmark), i.e.
                how consistently the strategy diverges from the benchmark.
        - ``Information Ratio``: [Information ratio](https://en.wikipedia.org/wiki/Information_ratio)
                — annualized active return divided by tracking error, i.e. consistency of
                benchmark-beating performance.
        - ``Periods``: Number of aligned return observations used.
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


#: Metric names included by ``metrics(mode="basic")``; the full set is always
#: computed and filtered down, so both modes stay consistent.
_METRICS_BASIC_ROWS = frozenset(
    {
        "Risk-Free Rate", "Time in Market",
        "Cumulative Return", "CAGR",
        "Sharpe", "Sortino", "Calmar", "Omega",
        "Volatility (ann.)", "Skew", "Kurtosis", "Historical VaR (95%)", "Historical Expected Shortfall (95%)",
        "Max Drawdown", "Longest DD Days", "Recovery Factor",
        "Payoff Ratio", "Profit Factor", "Tail Ratio",
        "MTD", "3M", "6M", "YTD", "1Y", "3Y (ann.)", "5Y (ann.)", "10Y (ann.)", "All-time (ann.)",
        "Best Day", "Worst Day", "Best Month", "Worst Month", "Best Year", "Worst Year",
        "Win Days", "Win Month", "Win Year",
        "Beta", "Alpha", "Correlation", "R²", "Information Ratio", "Tracking Error", "Treynor Ratio",
    }
)


def metrics(
    returns: pd.Series,
    benchmark: pd.Series | None = None,
    *,
    mode: Literal["basic", "full"] = "full",
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
    rf: float = 0.0,
) -> pd.DataFrame:
    """Build the full quantstats-style metrics table for a return stream.

    Composes the individual `q.stats` metric functions into one grouped
    DataFrame — the table behind :func:`qrt.plot.metrics_table` and the
    tearsheet's metrics panel. Values are raw (floats, ints, timestamps),
    not formatted strings; rendering/formatting is left to the caller.

    Args:
        returns: Strategy periodic return series with a ``DatetimeIndex``.
        benchmark: Optional benchmark periodic return series, aligned to
            ``returns`` on shared dates. Adds a benchmark column plus a
            ``vs. Benchmark`` section (Beta, Alpha, Correlation, R²,
            Information Ratio, Tracking Error, Treynor Ratio) filled only
            for the strategy column.
        mode: ``"full"`` (default) for every metric, ``"basic"`` for a
            compact headline subset.
        return_type: Whether ``returns``/``benchmark`` are ``"simple"`` or
            ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.
        rf: Annualized risk-free rate, used by excess-return metrics and
            reported in the ``Risk-Free Rate`` row. Defaults to ``0.0``.

    Returns:
        DataFrame with a ``(Section, Metric)`` ``MultiIndex`` and one column
        per series (benchmark first when given). Sections: ``Overview``,
        ``Returns``, ``Risk-Adjusted``, ``Risk``, ``Drawdown``, ``Trading``,
        ``Period Returns``, ``Best / Worst``, ``Win Rates``, and
        ``vs. Benchmark`` (benchmark only).
    """
    if mode not in ("basic", "full"):
        raise ValueError("mode must be 'basic' or 'full'")
    if benchmark is not None:
        strategy, reference = _aligned_returns(returns, benchmark, return_type)
    else:
        strategy, reference = _simple_returns(returns, return_type, "Strategy"), None
    periods = _periods_per_year(periods_per_year, strategy.index)

    def compute(series: pd.Series) -> dict[tuple[str, str], object]:
        episodes = drawdown_details(series, sort_by="depth")
        deepest = episodes.iloc[0] if len(episodes) else None
        rows: dict[tuple[str, str], object] = {
            ("Overview", "Risk-Free Rate"): rf,
            ("Overview", "Time in Market"): exposure(series),
            ("Returns", "Cumulative Return"): float((1.0 + series).prod() - 1.0),
            ("Returns", "CAGR"): float(_cagr(_excess_returns(series, rf, periods), periods)),
            ("Returns", "Expected Daily"): expected_return(series),
            ("Returns", "Expected Monthly"): expected_return(series, aggregate="M"),
            ("Returns", "Expected Yearly"): expected_return(series, aggregate="Y"),
            ("Risk-Adjusted", "Sharpe"): sharpe(series, periods_per_year=periods, rf=rf),
            ("Risk-Adjusted", "Prob. Sharpe Ratio"): probabilistic_ratio(series, base="sharpe", periods_per_year=periods, rf=rf),
            ("Risk-Adjusted", "Smart Sharpe"): sharpe(series, periods_per_year=periods, rf=rf, smart=True),
            ("Risk-Adjusted", "Sortino"): sortino(series, periods_per_year=periods, rf=rf),
            ("Risk-Adjusted", "Smart Sortino"): sortino(series, periods_per_year=periods, rf=rf, smart=True),
            ("Risk-Adjusted", "Sortino/√2"): adjusted_sortino(series, periods_per_year=periods, rf=rf),
            ("Risk-Adjusted", "Smart Sortino/√2"): adjusted_sortino(series, periods_per_year=periods, rf=rf, smart=True),
            ("Risk-Adjusted", "Omega"): omega(series, periods_per_year=periods, rf=rf),
            ("Risk-Adjusted", "Calmar"): calmar(series, periods_per_year=periods, rf=rf),
            ("Risk", "Volatility (ann.)"): volatility(series, periods_per_year=periods),
            ("Risk", "Skew"): skew(series),
            ("Risk", "Kurtosis"): kurtosis(series),
            ("Risk", "Historical VaR (95%)"): historical_value_at_risk(series),
            ("Risk", "Historical Expected Shortfall (95%)"): historical_expected_shortfall(series),
            ("Risk", "Kelly Criterion"): kelly_criterion(series),
            ("Risk", "Risk of Ruin"): risk_of_ruin(series),
            ("Drawdown", "Max Drawdown"): max_drawdown(series),
            ("Drawdown", "Max DD Date"): deepest["Valley"] if deepest is not None else pd.NaT,
            ("Drawdown", "Max DD Period Start"): deepest["Start"] if deepest is not None else pd.NaT,
            ("Drawdown", "Max DD Period End"): deepest["End"] if deepest is not None else pd.NaT,
            ("Drawdown", "Longest DD Days"): int(episodes["Days"].max()) if len(episodes) else float("nan"),
            ("Drawdown", "Avg. Drawdown"): float(episodes["Max Drawdown"].mean()) if len(episodes) else float("nan"),
            ("Drawdown", "Avg. Drawdown Days"): float(episodes["Days"].mean()) if len(episodes) else float("nan"),
            ("Drawdown", "Recovery Factor"): recovery_factor(series),
            ("Drawdown", "Ulcer Index"): ulcer_index(series),
            ("Drawdown", "Serenity Index"): serenity_index(series),
            ("Trading", "Max Consecutive Wins"): consecutive_wins(series),
            ("Trading", "Max Consecutive Losses"): consecutive_losses(series),
            ("Trading", "Gain/Pain Ratio"): gain_to_pain_ratio(series, periods_per_year=periods, rf=rf),
            ("Trading", "Gain/Pain (1M)"): gain_to_pain_ratio(series, rf=rf, aggregate="M"),
            ("Trading", "Payoff Ratio"): payoff_ratio(series),
            ("Trading", "Profit Factor"): profit_factor(series),
            ("Trading", "Common Sense Ratio"): common_sense_ratio(series),
            ("Trading", "CPC Index"): cpc_index(series),
            ("Trading", "Tail Ratio"): tail_ratio(series),
            ("Trading", "Outlier Win Ratio"): outlier_win_ratio(series),
            ("Trading", "Outlier Loss Ratio"): outlier_loss_ratio(series),
        }
        for label, value in period_returns(series, periods_per_year=periods).items():
            rows[("Period Returns", label)] = value
        rows.update(
            {
                ("Best / Worst", "Best Day"): best(series),
                ("Best / Worst", "Worst Day"): worst(series),
                ("Best / Worst", "Best Month"): best(series, aggregate="M"),
                ("Best / Worst", "Worst Month"): worst(series, aggregate="M"),
                ("Best / Worst", "Best Year"): best(series, aggregate="Y"),
                ("Best / Worst", "Worst Year"): worst(series, aggregate="Y"),
                ("Win Rates", "Win Days"): win_rate(series),
                ("Win Rates", "Win Month"): win_rate(series, aggregate="M"),
                ("Win Rates", "Win Quarter"): win_rate(series, aggregate="Q"),
                ("Win Rates", "Win Year"): win_rate(series, aggregate="Y"),
                ("Win Rates", "Avg. Up Month"): avg_win(series, aggregate="M"),
                ("Win Rates", "Avg. Down Month"): avg_loss(series, aggregate="M"),
            }
        )
        return rows

    strategy_name = str(strategy.name or "Strategy")
    strategy_rows = compute(strategy)
    if reference is not None:
        relative = benchmark_stats(strategy, reference, periods_per_year=periods)
        strategy_rows.update(
            {
                ("vs. Benchmark", "Beta"): float(relative["Beta"]),
                ("vs. Benchmark", "Alpha"): float(relative["Alpha"]),
                ("vs. Benchmark", "Correlation"): float(relative["Correlation"]),
                ("vs. Benchmark", "R²"): r_squared(strategy, reference),
                ("vs. Benchmark", "Information Ratio"): float(relative["Information Ratio"]),
                ("vs. Benchmark", "Tracking Error"): float(relative["Tracking Error"]),
                ("vs. Benchmark", "Treynor Ratio"): treynor_ratio(strategy, reference, periods_per_year=periods, rf=rf),
            }
        )
        benchmark_name = str(reference.name or "Benchmark")
        frame = pd.DataFrame({benchmark_name: compute(reference), strategy_name: strategy_rows})
    else:
        frame = pd.DataFrame({strategy_name: strategy_rows})
    frame = frame.reindex(list(strategy_rows))
    frame.index = pd.MultiIndex.from_tuples(frame.index, names=["Section", "Metric"])
    if mode == "basic":
        frame = frame[frame.index.get_level_values("Metric").isin(_METRICS_BASIC_ROWS)]
    return frame


def to_drawdown_series(returns: pd.Series, *, return_type: ReturnType = "simple") -> pd.Series:
    """Convert a return series into its running drawdown series.

    Each value is the percentage decline from the running peak of cumulative growth (0 at new
    highs, negative during drawdowns).

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Drawdown series (non-positive values), same index as ``returns``.
    """
    series = _simple_returns(returns, return_type)
    curve = (1.0 + series).cumprod()
    return curve.div(curve.cummax().clip(lower=1.0)).sub(1.0).rename(f"{series.name} drawdown")


def max_drawdown(returns: pd.Series, *, return_type: ReturnType = "simple") -> float:
    """Calculate the maximum [drawdown](https://en.wikipedia.org/wiki/Drawdown_(economics)).

    The largest peak-to-trough decline in cumulative value over the period. See
    :func:`to_drawdown_series` for the full running series.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Max Drawdown (a non-positive number, e.g. ``-0.25`` for a 25% decline).
    """
    return float(to_drawdown_series(returns, return_type=return_type).min())


def drawdown_details(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    sort_by: Literal["depth", "duration"] = "depth",
) -> pd.DataFrame:
    """Break a return stream's drawdown series into individual peak-to-recovery episodes.

    A prerequisite for `q.plot`'s longest-drawdown highlighting. See :func:`to_drawdown_series`
    for the underlying running drawdown series.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        sort_by: Order episodes by ``"depth"`` (deepest drawdown first, default) or
            ``"duration"`` (longest first).

    Returns:
        DataFrame with one row per drawdown episode and columns:

        - ``Start``: Last date at a new high before the decline began.
        - ``Valley``: Date of the deepest point of the drawdown.
        - ``End``: Last date the drawdown was still active (before recovering to a new high,
                or the final date in ``returns`` if the drawdown never recovered).
        - ``Days``: Number of calendar days from ``Start`` to ``End``.
        - ``Max Drawdown``: The episode's trough value (a non-positive number).

        Empty (no rows) if ``returns`` never drew down.
    """
    drawdown = to_drawdown_series(returns, return_type=return_type)
    if not isinstance(drawdown.index, pd.DatetimeIndex):
        raise TypeError("returns must have a DatetimeIndex for drawdown episode duration")

    underwater = drawdown < 0.0
    if not underwater.any():
        return pd.DataFrame(columns=["Start", "Valley", "End", "Days", "Max Drawdown"])

    episode_id = (underwater != underwater.shift(1, fill_value=False)).cumsum()
    episodes = []
    for _, group in drawdown[underwater].groupby(episode_id[underwater]):
        loc = drawdown.index.get_loc(group.index[0])
        start = drawdown.index[loc - 1] if loc > 0 else group.index[0]
        end = group.index[-1]
        episodes.append(
            {
                "Start": start,
                "Valley": group.idxmin(),
                "End": end,
                "Days": (end - start).days,
                "Max Drawdown": float(group.min()),
            }
        )

    table = pd.DataFrame(episodes)
    sort_col = "Max Drawdown" if sort_by == "depth" else "Days"
    return table.sort_values(sort_col, ascending=sort_by == "depth").reset_index(drop=True)


def volatility(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
) -> float:
    """Calculate annualized [volatility](https://en.wikipedia.org/wiki/Volatility_(finance)).

    The standard deviation of returns — the most common measure of risk. See
    :func:`rolling_volatility` for a moving-window variant.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.

    Returns:
        Annualized volatility.
    """
    series = _simple_returns(returns, return_type)
    if len(series) < 2:
        return float("nan")
    periods = _periods_per_year(periods_per_year, series.index)
    return float(series.std(ddof=1) * periods**0.5)


def calmar(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
    rf: float = 0.0,
) -> float:
    """Calculate the [Calmar ratio](https://en.wikipedia.org/wiki/Calmar_ratio).

    CAGR divided by the absolute Max Drawdown, i.e. return per unit of worst-case pain endured.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.
        rf: Annualized risk-free rate, subtracted (after deannualizing) from
            returns before computing CAGR. Defaults to ``0.0``.

    Returns:
        Calmar ratio.
    """
    series = _simple_returns(returns, return_type)
    periods = _periods_per_year(periods_per_year, series.index)
    excess = _excess_returns(series, rf, periods)
    drawdown = max_drawdown(series, return_type="simple")
    return _cagr(excess, periods) / abs(drawdown) if drawdown else float("nan")


def win_rate(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    aggregate: Literal["W", "M", "Q", "Y"] | None = None,
) -> float:
    """Calculate the win rate: the share of non-zero-return periods that were positive.

    Periods with exactly zero return are excluded from both the count of wins and the total.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        aggregate: Optional calendar period to compound into first (see
            :func:`aggregate_returns`), e.g. ``"M"`` for the share of winning months.

    Returns:
        Win rate (0-1 scale).
    """
    series = _simple_returns(returns, return_type)
    if aggregate is not None:
        series = aggregate_returns(series, aggregate)
    non_zero = series[series != 0]
    return float((non_zero > 0).mean()) if len(non_zero) else float("nan")


def information_ratio(
    returns: pd.Series,
    benchmark: pd.Series,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
) -> float:
    """Calculate the [Information ratio](https://en.wikipedia.org/wiki/Information_ratio).

    Annualized active return (strategy minus benchmark) divided by tracking error, i.e.
    consistency of benchmark-beating performance.

    Args:
        returns: Strategy periodic return series.
        benchmark: Benchmark periodic return series, aligned on shared dates.
        return_type: Whether ``returns``/``benchmark`` are ``"simple"`` or
            ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.

    Returns:
        Information Ratio.
    """
    strategy, reference = _aligned_returns(returns, benchmark, return_type)
    periods = _periods_per_year(periods_per_year, strategy.index)
    active = strategy - reference
    tracking_error = active.std(ddof=1) if len(active) > 1 else float("nan")
    return float(active.mean() / tracking_error * periods**0.5) if tracking_error else float("nan")


def excess_returns(
    returns: pd.Series,
    rf: float = 0.0,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
) -> pd.Series:
    """Calculate per-period excess returns over a deannualized risk-free rate.

    ``rf`` is an annualized rate; it is converted to a per-period rate before being subtracted
    from each period's return (see :func:`performance`'s ``rf`` parameter for the same convention).

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        rf: Annualized risk-free rate. Defaults to ``0.0`` (returns unchanged).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency used to deannualize ``rf``.
            Inferred from the index when not given.

    Returns:
        Excess return series.
    """
    series = _simple_returns(returns, return_type)
    periods = _periods_per_year(periods_per_year, series.index)
    return _excess_returns(series, rf, periods).rename(f"{series.name} excess")


def to_log_returns(returns: pd.Series, *, return_type: ReturnType = "simple") -> pd.Series:
    """Convert a return series to log (continuously compounded) returns.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Log return series (``ln(1 + returns)``).
    """
    series = _simple_returns(returns, return_type)
    return np.log1p(series).rename(f"{series.name} log returns")


def exponential_volatility(
    returns: pd.Series,
    span: int = 30,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
    annualize: bool = True,
) -> pd.Series:
    """Calculate exponentially-weighted volatility, giving more weight to recent returns.

    Unlike :func:`rolling_volatility`'s fixed window with equal weighting, each observation's
    influence decays geometrically with age, controlled by ``span``.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        span: Decay span (same semantics as ``pandas.Series.ewm``); roughly the
            number of recent periods that dominate the estimate.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.
        annualize: Whether to annualize the result. Defaults to ``True``.

    Returns:
        Series of (optionally annualized) exponentially-weighted volatility.
    """
    series = _simple_returns(returns, return_type)
    if span < 2:
        raise ValueError("span must be at least 2")
    ewm_std = series.ewm(span=span, min_periods=span).std()
    if annualize:
        periods = _periods_per_year(periods_per_year, series.index)
        ewm_std = ewm_std * periods**0.5
    return ewm_std.rename(f"{series.name} exponential volatility")


def geometric_mean(returns: pd.Series, *, return_type: ReturnType = "simple") -> float:
    """Calculate the [geometric mean](https://en.wikipedia.org/wiki/Geometric_mean) return per period.

    The constant per-period return that would produce the same compounded growth as the actual
    return sequence (the un-annualized building block of :func:`_cagr`).

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Geometric mean return per period.
    """
    series = _simple_returns(returns, return_type)
    return float((1.0 + series).prod() ** (1.0 / len(series)) - 1.0)


def expected_return(
    returns: pd.Series,
    *,
    aggregate: Literal["W", "M", "Q", "Y"] | None = None,
    return_type: ReturnType = "simple",
) -> float:
    """Calculate the geometric-mean expected return per period, optionally per calendar period.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        aggregate: Optional calendar period to compound into first (see
            :func:`aggregate_returns`), e.g. ``"M"`` for the expected monthly return.
            ``None`` (default) uses the series' native frequency.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Geometric mean return per (aggregated) period.
    """
    series = _simple_returns(returns, return_type)
    if aggregate is not None:
        series = aggregate_returns(series, aggregate)
    return geometric_mean(series)


def outliers(returns: pd.Series, quantile: float = 0.95, *, return_type: ReturnType = "simple") -> pd.Series:
    """Return the subset of returns above a given quantile threshold.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        quantile: Quantile threshold, e.g. ``0.95`` for the top 5% of returns.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Returns above the ``quantile`` threshold.
    """
    series = _simple_returns(returns, return_type)
    return series[series > series.quantile(quantile)]


def remove_outliers(returns: pd.Series, quantile: float = 0.95, *, return_type: ReturnType = "simple") -> pd.Series:
    """Return the subset of returns below a given quantile threshold, discarding upper-tail outliers.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        quantile: Quantile threshold, e.g. ``0.95`` to discard the top 5% of returns.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Returns below the ``quantile`` threshold.
    """
    series = _simple_returns(returns, return_type)
    return series[series < series.quantile(quantile)]


def autocorr_penalty(returns: pd.Series, *, return_type: ReturnType = "simple") -> float:
    """Calculate a penalty factor for return autocorrelation.

    Serially correlated returns (e.g. from stale pricing, smoothing, or illiquid assets)
    understate true volatility and can artificially inflate Sharpe- and Sortino-style ratios.
    This factor (>= 1) is meant to multiply the ratio's denominator to correct for that; see
    ``smart=True`` on :func:`sharpe`/:func:`sortino`.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Autocorrelation penalty factor (``1.0`` when lag-1 autocorrelation is zero or undefined).
    """
    series = _simple_returns(returns, return_type)
    n = len(series)
    if n < 3:
        return 1.0
    coef = abs(np.corrcoef(series.iloc[:-1], series.iloc[1:])[0, 1])
    if not np.isfinite(coef):
        return 1.0
    lags = np.arange(1, n)
    terms = ((n - lags) / n) * (coef**lags)
    return float(np.sqrt(1.0 + 2.0 * terms.sum()))


def sharpe(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
    rf: float = 0.0,
    smart: bool = False,
) -> float:
    """Calculate the annualized Sharpe ratio of excess returns.

    The [Sharpe ratio](https://en.wikipedia.org/wiki/Sharpe_ratio) is the annualized mean excess
    return divided by the annualized volatility of returns — return earned per unit of total risk
    taken.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.
        rf: Annualized risk-free rate, subtracted (after deannualizing) from
            returns before computing the ratio. Defaults to ``0.0``.
        smart: Whether to penalize the denominator for return autocorrelation via
            :func:`autocorr_penalty`, which otherwise inflates the ratio for serially correlated
            (e.g. smoothed or illiquid) return streams. Defaults to ``False``.

    Returns:
        Annualized Sharpe ratio.
    """
    series = _simple_returns(returns, return_type)
    periods = _periods_per_year(periods_per_year, series.index)
    excess = _excess_returns(series, rf, periods)
    volatility = excess.std(ddof=1) if len(excess) > 1 else float("nan")
    if smart and np.isfinite(volatility):
        volatility *= autocorr_penalty(series, return_type="simple")
    return excess.mean() / volatility * periods**0.5 if volatility else float("nan")


def sortino(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
    rf: float = 0.0,
    smart: bool = False,
) -> float:
    """Calculate the annualized Sortino ratio of excess returns.

    The [Sortino ratio](https://en.wikipedia.org/wiki/Sortino_ratio) is like the Sharpe ratio, but
    only penalizes downside volatility, since investors rarely mind upside swings.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.
        rf: Annualized risk-free rate, subtracted (after deannualizing) from
            returns before computing the ratio. Defaults to ``0.0``.
        smart: Whether to penalize the denominator for return autocorrelation, see
            :func:`autocorr_penalty`. Defaults to ``False``.

    Returns:
        Annualized Sortino ratio.
    """
    series = _simple_returns(returns, return_type)
    periods = _periods_per_year(periods_per_year, series.index)
    excess = _excess_returns(series, rf, periods)
    downside_deviation = np.sqrt(np.mean(np.minimum(excess.to_numpy(), 0.0) ** 2))
    if smart and downside_deviation:
        downside_deviation *= autocorr_penalty(series, return_type="simple")
    return excess.mean() / downside_deviation * periods**0.5 if downside_deviation else float("nan")


def adjusted_sortino(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
    rf: float = 0.0,
    smart: bool = False,
) -> float:
    """Calculate Jack Schwager's adjusted Sortino ratio.

    Divides the [Sortino ratio](https://en.wikipedia.org/wiki/Sortino_ratio) by
    $\\sqrt{2}$ so it can be compared directly against the Sharpe ratio, which otherwise tends to
    run higher since it divides by an unconditional rather than downside-only deviation.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.
        rf: Annualized risk-free rate, subtracted (after deannualizing) from
            returns before computing the ratio. Defaults to ``0.0``.
        smart: Whether to penalize for return autocorrelation, see :func:`sortino`.

    Returns:
        Adjusted Sortino ratio.
    """
    return (
        sortino(returns, return_type=return_type, periods_per_year=periods_per_year, rf=rf, smart=smart)
        / 2.0**0.5
    )


def probabilistic_ratio(
    returns: pd.Series,
    *,
    base: Literal["sharpe", "sortino", "adjusted_sortino"] = "sharpe",
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
    rf: float = 0.0,
    smart: bool = False,
) -> float:
    """Calculate the probability that a risk-adjusted ratio is truly positive.

    The Probabilistic Sharpe Ratio (Bailey & Lopez de Prado, 2012) converts a point-estimate ratio
    into a confidence level by accounting for sample size, skew, and kurtosis, all of which affect
    how noisy the ratio estimate is. The same correction is applied here to the Sortino and
    adjusted-Sortino ratios.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        base: Which ratio to convert: ``"sharpe"``, ``"sortino"``, or ``"adjusted_sortino"``.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.
        rf: Annualized risk-free rate, subtracted (after deannualizing) from
            returns before computing the base ratio. Defaults to ``0.0``.
        smart: Whether to penalize the base ratio for return autocorrelation, see
            :func:`sharpe`/:func:`sortino`.

    Returns:
        Probability (0-1) that the true ratio is greater than zero.
    """
    if base not in ("sharpe", "sortino", "adjusted_sortino"):
        raise ValueError("base must be one of 'sharpe', 'sortino', or 'adjusted_sortino'")
    series = _simple_returns(returns, return_type)
    periods = _periods_per_year(periods_per_year, series.index)
    base_fn = {"sharpe": sharpe, "sortino": sortino, "adjusted_sortino": adjusted_sortino}[base]
    annualized = base_fn(series, periods_per_year=periods, rf=rf, smart=smart)
    ratio = annualized / periods**0.5
    n = len(series)
    if n < 2 or not np.isfinite(ratio):
        return float("nan")
    skewness = float(series.skew())
    kurtosis_raw = float(series.kurtosis()) + 3.0
    variance = 1.0 - skewness * ratio + (kurtosis_raw - 1.0) / 4.0 * ratio**2
    if variance <= 0:
        return float("nan")
    z = ratio * (n - 1) ** 0.5 / variance**0.5
    return float(norm.cdf(z))


def treynor_ratio(
    returns: pd.Series,
    benchmark: pd.Series,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
    rf: float = 0.0,
) -> float:
    """Calculate the annualized Treynor ratio relative to a benchmark.

    The [Treynor ratio](https://en.wikipedia.org/wiki/Treynor_ratio) is the annualized mean excess
    return divided by beta — like the Sharpe ratio, but measuring return earned per unit of
    systematic (market) risk rather than total risk.

    Args:
        returns: Strategy periodic return series.
        benchmark: Benchmark periodic return series, aligned on shared dates.
        return_type: Whether ``returns``/``benchmark`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.
        rf: Annualized risk-free rate, subtracted (after deannualizing) from
            returns before computing the ratio. Defaults to ``0.0``.

    Returns:
        Annualized Treynor ratio.
    """
    strategy, reference = _aligned_returns(returns, benchmark, return_type)
    periods = _periods_per_year(periods_per_year, strategy.index)
    excess = _excess_returns(strategy, rf, periods)
    beta_value = beta(strategy, reference, return_type="simple")
    return excess.mean() * periods / beta_value if beta_value and np.isfinite(beta_value) else float("nan")


def omega(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
    rf: float = 0.0,
    required_return: float = 0.0,
) -> float:
    """Calculate the Omega ratio of a return stream.

    The [Omega ratio](https://en.wikipedia.org/wiki/Omega_ratio) is the probability-weighted ratio
    of gains above a required-return threshold to losses below it, using the full return
    distribution rather than just its mean and variance (unlike Sharpe/Sortino).

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.
        rf: Annualized risk-free rate, subtracted (after deannualizing) from
            returns before computing the ratio. Defaults to ``0.0``.
        required_return: Annualized minimum acceptable return threshold, deannualized the same
            way as ``rf``. Defaults to ``0.0``.

    Returns:
        Omega ratio.
    """
    series = _simple_returns(returns, return_type)
    periods = _periods_per_year(periods_per_year, series.index)
    excess = _excess_returns(series, rf, periods)
    threshold = (1.0 + required_return) ** (1.0 / periods) - 1.0 if required_return else 0.0
    diff = excess - threshold
    gains = diff[diff > 0].sum()
    losses = -diff[diff < 0].sum()
    return gains / losses if losses else float("nan")


def gain_to_pain_ratio(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
    rf: float = 0.0,
    aggregate: Literal["W", "M", "Q", "Y"] | None = None,
) -> float:
    """Calculate Jack Schwager's Gain-to-Pain ratio.

    Sum of all (excess) returns divided by the absolute sum of losing periods — a simple measure
    of total profit generated per unit of total loss endured, without regard to distribution shape
    or timing.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency, used to deannualize ``rf``. Inferred from the
            index (after any ``aggregate`` compounding) when not given.
        rf: Annualized risk-free rate, subtracted (after deannualizing) from returns. Defaults to
            ``0.0``.
        aggregate: Optional calendar period to compound into first (see
            :func:`aggregate_returns`), e.g. ``"M"`` for the monthly-resolution ratio.

    Returns:
        Gain-to-Pain ratio.
    """
    series = _simple_returns(returns, return_type)
    if aggregate is not None:
        series = aggregate_returns(series, aggregate)
        periods_per_year = None
    periods = _periods_per_year(periods_per_year, series.index)
    excess = _excess_returns(series, rf, periods)
    losses = -excess[excess < 0].sum()
    return excess.sum() / losses if losses else float("nan")


def exposure(returns: pd.Series, *, return_type: ReturnType = "simple") -> float:
    """Calculate the fraction of periods with a non-zero return (time in market).

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Share of periods with a non-zero return, in ``[0, 1]``.
    """
    series = _simple_returns(returns, return_type)
    return float((series != 0).mean())


def rar(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
    rf: float = 0.0,
) -> float:
    """Calculate the Risk-Adjusted Return (CAGR divided by exposure).

    Divides CAGR by :func:`exposure` (the fraction of periods actually invested, i.e. with
    non-zero returns), so a strategy that earns its return while sitting in cash most of the time
    scores higher than one that needed to be fully invested throughout.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.
        rf: Annualized risk-free rate, subtracted (after deannualizing) from
            returns before computing CAGR. Defaults to ``0.0``.

    Returns:
        Risk-adjusted return.
    """
    series = _simple_returns(returns, return_type)
    periods = _periods_per_year(periods_per_year, series.index)
    excess = _excess_returns(series, rf, periods)
    time_in_market = exposure(series, return_type="simple")
    return _cagr(excess, periods) / time_in_market if time_in_market else float("nan")


def skew(returns: pd.Series, *, return_type: ReturnType = "simple") -> float:
    """Calculate the [skewness](https://en.wikipedia.org/wiki/Skewness) of returns.

    Skewness measures the degree of asymmetry of the return distribution around its mean.
    Positive skew means a longer right tail (occasional large gains); negative skew means a longer
    left tail (occasional large losses).

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Sample skewness.
    """
    series = _simple_returns(returns, return_type)
    return float(series.skew())


def kurtosis(returns: pd.Series, *, return_type: ReturnType = "simple") -> float:
    """Calculate the excess [kurtosis](https://en.wikipedia.org/wiki/Kurtosis) of returns.

    Kurtosis measures how fat-tailed the return distribution is relative to a normal distribution
    (which has an excess kurtosis of 0). Higher values mean more frequent extreme returns than a
    normal distribution would predict.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Sample excess kurtosis.
    """
    series = _simple_returns(returns, return_type)
    return float(series.kurtosis())


def ulcer_index(returns: pd.Series, *, return_type: ReturnType = "simple") -> float:
    """Calculate the Ulcer Index.

    The [Ulcer Index](https://en.wikipedia.org/wiki/Ulcer_index) is the root-mean-square of
    drawdowns from the running peak, capturing both the depth and duration of drawdowns rather
    than just their worst point (unlike Max Drawdown).

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Ulcer Index.
    """
    series = _simple_returns(returns, return_type)
    curve = (1.0 + series).cumprod()
    drawdown = curve.div(curve.cummax().clip(lower=1.0)).sub(1.0)
    return float(np.sqrt((drawdown**2).mean()))


def ulcer_performance_index(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    periods_per_year: int | None = None,
    rf: float = 0.0,
) -> float:
    """Calculate the Ulcer Performance Index (Martin ratio).

    Annualized excess return divided by the :func:`ulcer_index` — like Calmar, but risk is
    measured by the depth *and* duration of drawdowns rather than just the single worst one.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        periods_per_year: Annualization frequency. Inferred from the index
            when not given.
        rf: Annualized risk-free rate, subtracted (after deannualizing) from
            returns before computing CAGR. Defaults to ``0.0``.

    Returns:
        Ulcer Performance Index.
    """
    series = _simple_returns(returns, return_type)
    periods = _periods_per_year(periods_per_year, series.index)
    excess = _excess_returns(series, rf, periods)
    ulcer = ulcer_index(series, return_type="simple")
    return _cagr(excess, periods) / ulcer if ulcer else float("nan")


def serenity_index(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    rf: float = 0.0,
) -> float:
    """Calculate the Serenity Index.

    A composite drawdown-aware risk-adjusted return measure (KeyQuant, 2011): total excess return
    divided by the :func:`ulcer_index` scaled by a "pitfall" factor — the tail risk of drawdowns
    (their Conditional VaR) relative to overall return volatility. Penalizes strategies whose
    drawdowns are both deep/prolonged (high Ulcer Index) and concentrated in a few severe episodes
    (high pitfall).

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        rf: Amount subtracted from total return before dividing. Defaults to ``0.0``.

    Returns:
        Serenity Index.
    """
    series = _simple_returns(returns, return_type)
    curve = (1.0 + series).cumprod()
    drawdown = curve.div(curve.cummax().clip(lower=1.0)).sub(1.0)
    std_returns = series.std(ddof=1) if len(series) > 1 else float("nan")
    if not std_returns or not np.isfinite(std_returns):
        return float("nan")
    pitfall = historical_expected_shortfall(drawdown) / std_returns
    ulcer = float(np.sqrt((drawdown**2).mean()))
    denominator = ulcer * pitfall
    return (series.sum() - rf) / denominator if denominator else float("nan")


def risk_of_ruin(returns: pd.Series, *, return_type: ReturnType = "simple") -> float:
    """Estimate the risk of ruin.

    The [risk of ruin](https://en.wikipedia.org/wiki/Gambler%27s_ruin) is the probability of
    losing the entire trading account, from the classic gambler's-ruin formula applied to the
    strategy's per-period win rate.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Probability of ruin, in ``[0, 1]``.
    """
    series = _simple_returns(returns, return_type)
    non_zero = series[series != 0]
    win_rate = (non_zero > 0).mean() if len(non_zero) else float("nan")
    if not np.isfinite(win_rate):
        return float("nan")
    return float(((1.0 - win_rate) / (1.0 + win_rate)) ** len(series))


def tail_ratio(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    cutoff: float = 0.95,
) -> float:
    """Calculate the tail ratio between the right and left tails of the return distribution.

    Ratio of the ``cutoff`` percentile (e.g. 95th) to the ``1 - cutoff`` percentile (e.g. 5th) of
    returns — how large favorable outliers are relative to unfavorable ones.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        cutoff: Upper percentile used for the right tail; ``1 - cutoff`` is used for the left
            tail. Defaults to ``0.95``.

    Returns:
        Tail ratio.
    """
    series = _simple_returns(returns, return_type)
    upper = series.quantile(cutoff)
    lower = series.quantile(1.0 - cutoff)
    return float(abs(upper / lower)) if lower else float("nan")


def avg_return(returns: pd.Series, *, return_type: ReturnType = "simple") -> float:
    """Calculate the average return across non-zero periods.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Mean of non-zero periodic returns.
    """
    series = _simple_returns(returns, return_type)
    non_zero = series[series != 0]
    return float(non_zero.mean()) if len(non_zero) else float("nan")


def avg_win(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    aggregate: Literal["W", "M", "Q", "Y"] | None = None,
) -> float:
    """Calculate the average return across winning (positive-return) periods.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        aggregate: Optional calendar period to compound into first (see
            :func:`aggregate_returns`), e.g. ``"M"`` for the average up month.

    Returns:
        Mean of positive periodic returns.
    """
    series = _simple_returns(returns, return_type)
    if aggregate is not None:
        series = aggregate_returns(series, aggregate)
    wins = series[series > 0]
    return float(wins.mean()) if len(wins) else float("nan")


def avg_loss(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    aggregate: Literal["W", "M", "Q", "Y"] | None = None,
) -> float:
    """Calculate the average return across losing (negative-return) periods.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        aggregate: Optional calendar period to compound into first (see
            :func:`aggregate_returns`), e.g. ``"M"`` for the average down month.

    Returns:
        Mean of negative periodic returns.
    """
    series = _simple_returns(returns, return_type)
    if aggregate is not None:
        series = aggregate_returns(series, aggregate)
    losses = series[series < 0]
    return float(losses.mean()) if len(losses) else float("nan")


def payoff_ratio(returns: pd.Series, *, return_type: ReturnType = "simple") -> float:
    """Calculate the payoff ratio: average win divided by absolute average loss.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Payoff ratio.
    """
    series = _simple_returns(returns, return_type)
    loss = avg_loss(series, return_type="simple")
    win = avg_win(series, return_type="simple")
    return float(win / abs(loss)) if loss and np.isfinite(loss) else float("nan")


def profit_ratio(returns: pd.Series, *, return_type: ReturnType = "simple") -> float:
    """Calculate the profit ratio: win frequency divided by loss frequency.

    Distinct from :func:`payoff_ratio` (which compares win/loss *size*) and :func:`profit_factor`
    (which compares total gains vs. total losses) — this compares how often the strategy wins vs.
    how often it loses.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Profit ratio.
    """
    series = _simple_returns(returns, return_type)
    non_zero = series[series != 0]
    if not len(non_zero):
        return float("nan")
    wins = int((non_zero > 0).sum())
    losses = int((non_zero < 0).sum())
    if not wins:
        return 0.0
    if not losses:
        return float("nan")
    return float(wins / losses)


def profit_factor(returns: pd.Series, *, return_type: ReturnType = "simple") -> float:
    """Calculate the profit factor: total gains divided by total losses.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Profit factor.
    """
    series = _simple_returns(returns, return_type)
    gains = series[series > 0].sum()
    losses = abs(series[series < 0].sum())
    if not losses:
        return float("inf") if gains else float("nan")
    return float(gains / losses)


def cpc_index(returns: pd.Series, *, return_type: ReturnType = "simple") -> float:
    """Calculate the CPC Index: Profit Factor x Win Rate x Payoff Ratio.

    A composite score combining how much is won per unit lost (:func:`profit_factor`), how often
    periods win (win rate), and the relative size of wins vs. losses (:func:`payoff_ratio`).

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        CPC Index.
    """
    series = _simple_returns(returns, return_type)
    non_zero = series[series != 0]
    win_rate = (non_zero > 0).mean() if len(non_zero) else float("nan")
    return float(profit_factor(series, return_type="simple") * win_rate * payoff_ratio(series, return_type="simple"))


def common_sense_ratio(returns: pd.Series, *, return_type: ReturnType = "simple") -> float:
    """Calculate the Common Sense Ratio: Profit Factor x Tail Ratio.

    Combines overall profitability (:func:`profit_factor`) with the shape of extreme returns
    (:func:`tail_ratio`), so it penalizes strategies with a poor tail-risk profile even if their
    average profit factor looks good.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Common Sense Ratio.
    """
    series = _simple_returns(returns, return_type)
    return float(profit_factor(series, return_type="simple") * tail_ratio(series, return_type="simple"))


def outlier_win_ratio(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    quantile: float = 0.99,
) -> float:
    """Calculate the outlier win ratio: a high quantile of returns vs. the average win.

    Ratio of the ``quantile`` (e.g. 99th percentile) return to the average winning return — how
    much a strategy's best outcomes are driven by rare, outsized wins rather than typical ones.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        quantile: Upper quantile used for the outlier threshold. Defaults to ``0.99``.

    Returns:
        Outlier win ratio.
    """
    series = _simple_returns(returns, return_type)
    win = avg_win(series, return_type="simple")
    return float(series.quantile(quantile) / win) if win and np.isfinite(win) else float("nan")


def outlier_loss_ratio(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    quantile: float = 0.01,
) -> float:
    """Calculate the outlier loss ratio: a low quantile of returns vs. the average loss.

    Ratio of the ``quantile`` (e.g. 1st percentile) return to the average losing return — how much
    a strategy's worst outcomes are driven by rare, outsized losses rather than typical ones.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        quantile: Lower quantile used for the outlier threshold. Defaults to ``0.01``.

    Returns:
        Outlier loss ratio.
    """
    series = _simple_returns(returns, return_type)
    loss = avg_loss(series, return_type="simple")
    return float(series.quantile(quantile) / loss) if loss and np.isfinite(loss) else float("nan")


def recovery_factor(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    rf: float = 0.0,
) -> float:
    """Calculate the recovery factor: total return divided by Max Drawdown.

    How many multiples of the worst peak-to-trough decline the strategy ultimately earned back —
    higher values mean faster, more complete recovery from drawdowns.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        rf: Amount subtracted from total return before dividing. Defaults to ``0.0``.

    Returns:
        Recovery factor.
    """
    series = _simple_returns(returns, return_type)
    curve = (1.0 + series).cumprod()
    total_return = curve.iloc[-1] - 1.0 - rf
    max_drawdown = curve.div(curve.cummax().clip(lower=1.0)).sub(1.0).min()
    return float(abs(total_return) / abs(max_drawdown)) if max_drawdown else float("nan")


def netto_number(
    profit: float,
    *,
    unit_of_risk: float,
    max_adverse_excursion: float,
) -> float:
    r"""Calculate profit relative to planned risk and realized adverse excursion.

    The Netto Number combines an ex-ante risk budget with an ex-post loss
    magnitude:

    $$
    \operatorname{Netto Number}
    = \frac{\text{Profit}}{(\text{Unit-of-Risk} + \text{MAE}) / 2}
    = \frac{2\,\text{Profit}}{\text{Unit-of-Risk} + \text{MAE}}.
    $$

    All three inputs must describe the same strategy and evaluation period in
    the same units, either currency amounts or fractions of starting capital.
    ``max_adverse_excursion`` is supplied explicitly because its original
    principal-relative convention is not necessarily the same as the standard
    peak-to-trough :func:`max_drawdown` calculated from a return stream.

    This ratio is descriptive, not a safe general optimization objective. When
    ``profit`` is negative, increasing ``max_adverse_excursion`` raises the
    result toward zero, so a worse losing path can rank above a less adverse
    one. Preserve the three components and use a risk-monotonic objective for
    training or policy selection.

    Args:
        profit: Net realized profit. May be positive, zero, or negative.
        unit_of_risk: Positive risk budget fixed before the evaluation period.
        max_adverse_excursion: Largest realized adverse excursion as a
            non-negative loss magnitude.

    Returns:
        Profit per blended unit of planned and realized risk.

    Raises:
        TypeError: If an input is not a scalar.
        ValueError: If an input is non-finite, ``unit_of_risk`` is not
            positive, or ``max_adverse_excursion`` is negative.
    """
    values = {
        "profit": profit,
        "unit_of_risk": unit_of_risk,
        "max_adverse_excursion": max_adverse_excursion,
    }
    normalized: dict[str, float] = {}
    for name, value in values.items():
        if isinstance(value, bool) or not np.isscalar(value):
            raise TypeError(f"{name} must be a scalar")
        normalized[name] = float(value)
        if not np.isfinite(normalized[name]):
            raise ValueError(f"{name} must be finite")

    if normalized["unit_of_risk"] <= 0.0:
        raise ValueError("unit_of_risk must be positive")
    if normalized["max_adverse_excursion"] < 0.0:
        raise ValueError("max_adverse_excursion must be non-negative")

    risk_factor = (
        normalized["unit_of_risk"] + normalized["max_adverse_excursion"]
    ) / 2.0
    return normalized["profit"] / risk_factor


def risk_return_ratio(returns: pd.Series, *, return_type: ReturnType = "simple") -> float:
    """Calculate the risk-return ratio: mean return divided by its standard deviation.

    Like the Sharpe ratio, but un-annualized and without a risk-free rate — the simplest possible
    return-per-unit-of-risk measure.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Risk-return ratio.
    """
    series = _simple_returns(returns, return_type)
    std = series.std(ddof=1) if len(series) > 1 else float("nan")
    return float(series.mean() / std) if std and np.isfinite(std) else float("nan")


def kelly_criterion(returns: pd.Series, *, return_type: ReturnType = "simple") -> float:
    """Calculate the Kelly Criterion fraction.

    The [Kelly Criterion](https://en.wikipedia.org/wiki/Kelly_criterion) is the recommended
    fraction of capital to allocate to a strategy given its win rate and :func:`payoff_ratio`, to
    maximize long-run geometric growth without risking ruin.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Kelly fraction (can be negative, indicating the strategy has negative expectancy).
    """
    series = _simple_returns(returns, return_type)
    non_zero = series[series != 0]
    win_rate = (non_zero > 0).mean() if len(non_zero) else float("nan")
    payoff = payoff_ratio(series, return_type="simple")
    if not payoff or not np.isfinite(payoff) or not np.isfinite(win_rate):
        return float("nan")
    return float((payoff * win_rate - (1.0 - win_rate)) / payoff)


def best(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    aggregate: Literal["W", "M", "Q", "Y"] | None = None,
) -> float:
    """Return the single best (highest) period return.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        aggregate: Optional calendar period to compound into first (see
            :func:`aggregate_returns`), e.g. ``"M"`` for the best month.

    Returns:
        Maximum periodic return.
    """
    series = _simple_returns(returns, return_type)
    if aggregate is not None:
        series = aggregate_returns(series, aggregate)
    return float(series.max())


def worst(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    aggregate: Literal["W", "M", "Q", "Y"] | None = None,
) -> float:
    """Return the single worst (lowest) period return.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        aggregate: Optional calendar period to compound into first (see
            :func:`aggregate_returns`), e.g. ``"M"`` for the worst month.

    Returns:
        Minimum periodic return.
    """
    series = _simple_returns(returns, return_type)
    if aggregate is not None:
        series = aggregate_returns(series, aggregate)
    return float(series.min())


def _max_consecutive(mask: pd.Series) -> int:
    """Return the longest run of consecutive ``True`` values in a boolean Series."""
    if not len(mask):
        return 0
    groups = (~mask).cumsum()
    streaks = mask.groupby(groups).sum()
    return int(streaks.max()) if len(streaks) else 0


def consecutive_wins(returns: pd.Series, *, return_type: ReturnType = "simple") -> int:
    """Return the longest streak of consecutive positive-return periods.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Length of the longest winning streak.
    """
    series = _simple_returns(returns, return_type)
    return _max_consecutive(series > 0)


def consecutive_losses(returns: pd.Series, *, return_type: ReturnType = "simple") -> int:
    """Return the longest streak of consecutive negative-return periods.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Length of the longest losing streak.
    """
    series = _simple_returns(returns, return_type)
    return _max_consecutive(series < 0)


def distribution(returns: pd.Series, *, return_type: ReturnType = "simple") -> dict[str, dict[str, list[float]]]:
    """Break down compounded returns by period, flagging IQR outliers within each.

    Compounds ``returns`` into Daily (as given), Weekly, Monthly, Quarterly, and Yearly buckets,
    then splits each bucket's values into "normal" and "outlier" using the standard 1.5x
    interquartile-range rule.

    Args:
        returns: Periodic return series with a ``DatetimeIndex``.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        Dict keyed by period name (``"Daily"``, ``"Weekly"``, ``"Monthly"``, ``"Quarterly"``,
        ``"Yearly"``), each mapping to ``{"values": [...], "outliers": [...]}``.
    """
    series = _simple_returns(returns, return_type)
    if not isinstance(series.index, pd.DatetimeIndex):
        raise TypeError("returns must have a DatetimeIndex for distribution analysis")

    def compound(group: pd.Series) -> float:
        return float((1.0 + group).prod() - 1.0)

    def split(values: pd.Series) -> dict[str, list[float]]:
        q1, q3 = values.quantile(0.25), values.quantile(0.75)
        iqr = q3 - q1
        within = (values >= q1 - 1.5 * iqr) & (values <= q3 + 1.5 * iqr)
        return {"values": values[within].tolist(), "outliers": values[~within].tolist()}

    return {
        "Daily": split(series),
        "Weekly": split(series.resample("W-MON").apply(compound)),
        "Monthly": split(series.resample("ME").apply(compound)),
        "Quarterly": split(series.resample("QE").apply(compound)),
        "Yearly": split(series.resample("YE").apply(compound)),
    }


def r_squared(returns: pd.Series, benchmark: pd.Series, *, return_type: ReturnType = "simple") -> float:
    """Calculate R² (coefficient of determination) between strategy and benchmark returns.

    [R²](https://en.wikipedia.org/wiki/Coefficient_of_determination) is the square of the Pearson
    correlation between strategy and benchmark returns — how much of the strategy's variance is
    explained by benchmark movements. Closer to 1 means the strategy moves in lockstep with the
    benchmark; closer to 0 means it's largely independent.

    Args:
        returns: Strategy periodic return series.
        benchmark: Benchmark periodic return series, aligned on shared dates.
        return_type: Whether ``returns``/``benchmark`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        R², in ``[0, 1]``.
    """
    strategy, reference = _aligned_returns(returns, benchmark, return_type)
    return float(strategy.corr(reference) ** 2)


def compare(returns: pd.Series, benchmark: pd.Series, *, return_type: ReturnType = "simple") -> pd.DataFrame:
    """Compare strategy and benchmark returns period-by-period.

    Args:
        returns: Strategy periodic return series.
        benchmark: Benchmark periodic return series, aligned on shared dates.
        return_type: Whether ``returns``/``benchmark`` are ``"simple"`` or ``"log"`` returns.

    Returns:
        DataFrame indexed like the aligned returns, with columns:

        - ``Strategy``: Strategy return for the period.
        - ``Benchmark``: Benchmark return for the period.
        - ``Multiplier``: ``Strategy / Benchmark`` for the period.
        - ``Won``: ``True`` where the strategy return met or beat the benchmark.
    """
    strategy, reference = _aligned_returns(returns, benchmark, return_type)
    return pd.DataFrame(
        {
            "Strategy": strategy,
            "Benchmark": reference,
            "Multiplier": strategy / reference.replace(0.0, np.nan),
            "Won": strategy >= reference,
        }
    )


def _stationary_bootstrap_indices(rng: np.random.Generator, pool_size: int, length: int, block_size: float) -> np.ndarray:
    """Build one circular stationary-bootstrap index sequence of the given ``length``.

    Implements the [Politis & Romano (1994)](https://doi.org/10.2307/2290993) stationary
    bootstrap: the sequence is stitched together out of contiguous, circularly-wrapped blocks
    drawn from a pool of ``pool_size`` source periods (a block can run off the end of the pool
    and continue from the start) whose lengths are drawn from a Geometric distribution with mean
    ``block_size``. Resampling contiguous runs instead of individual points preserves local
    autocorrelation and volatility clustering that an i.i.d. (point-by-point) bootstrap destroys,
    while the randomized (rather than fixed) block length keeps the resampled series statistically
    stationary — unlike a fixed-length moving-block bootstrap, it doesn't inject an artificial
    periodicity at the block boundary. ``length`` may differ from ``pool_size`` (e.g. simulating a
    shorter forward horizon than the historical sample used as the resampling pool).
    """
    indices = np.empty(length, dtype=np.int64)
    p = 1.0 / block_size
    filled = 0
    while filled < length:
        start = int(rng.integers(pool_size))
        run = min(int(rng.geometric(p)), length - filled)
        indices[filled : filled + run] = (start + np.arange(run)) % pool_size
        filled += run
    return indices


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
) -> dict[str, object]:
    """Simulate bootstrap-resampled return paths to gauge the range of plausible outcomes.

    Each simulated path is built by resampling the historical returns *with replacement*
    (a [bootstrap](https://en.wikipedia.org/wiki/Bootstrapping_(statistics))), then compounding
    them into a cumulative growth path. Useful for estimating how much of a strategy's realized
    performance could plausibly be attributed to chance, and what range of terminal outcomes and
    drawdowns a similar return distribution could plausibly produce.

    Note:
        This deliberately resamples *with* replacement rather than merely permuting (shuffling)
        the historical returns. A plain permutation only reorders the same fixed set of returns,
        and since compounding is a product, its terminal value ``prod(1 + r)`` is invariant to
        the order of the factors — every permuted path compounds to *exactly* the same terminal
        return as the original. That makes a permutation-only simulation's terminal-value spread,
        ``goal_probability``, degenerate (every path either meets the goal or none do) even
        though its *path shape* (and therefore Max Drawdown) still varies meaningfully. Bootstrap
        resampling avoids this: some returns are drawn more than once and others not at all, so
        the terminal value genuinely varies across simulations, making
        ``terminal_stats``/``goal_probability`` statistically meaningful.

    Note:
        By default (``block_size=None``) each period is resampled independently (i.i.d.), which
        implicitly assumes returns have no serial dependence. Real return series routinely
        violate that: volatility clustering (calm/turbulent periods cluster together),
        short-term autocorrelation, and macro-regime persistence are all well documented. i.i.d.
        resampling destroys these dependencies, which tends to *understate* tail risk (it can't
        produce a realistic run of consecutive bad days beyond what chance alone would predict).
        Pass ``block_size`` (e.g. ``20`` for roughly a trading month) to instead draw contiguous,
        circularly-wrapped blocks of historical returns with Geometrically-distributed lengths
        (mean ``block_size``) — a stationary block bootstrap — which preserves that local
        structure. Larger ``block_size`` preserves longer-range dependence at the cost of fewer
        effectively-independent blocks (and thus less path diversity) per simulation; it should
        typically be set to roughly the horizon over which returns are believed to be
        autocorrelated (e.g. the length of a typical volatility cluster). For explicitly modeling
        time-varying volatility/regime shifts, a fitted parametric model (ARMA-GARCH) is a more
        appropriate but heavier tool than resampling; that's out of scope here.

    Note:
        Compounding is multiplicative, so its variance accumulates with the number of resampled
        periods: simulating as many periods as a long history contains (the default,
        ``periods=None``) makes the terminal-value spread balloon (easily spanning multiple
        orders of magnitude for a volatile asset) and pushes any fixed ``bust``/``goal``
        threshold's probability toward 0% or 100%, since a long enough random path is nearly
        guaranteed to cross it at some point — both effects are real, not bugs, but make for a
        poorly-differentiated simulation. Pass ``periods`` to decouple the simulation horizon from
        the length of ``returns``: the full history is still used as the resampling pool (so a
        long, multi-regime history avoids biasing *what* gets resampled — see the module-level
        guidance on avoiding a single-regime sample), while each simulated path only covers
        ``periods`` steps forward, matching whatever horizon ``bust``/``goal`` are actually meant
        to evaluate (e.g. ``periods=252`` for one trading year). Must satisfy
        ``1 <= periods <= len(returns)``. When given, ``sim_0`` (the "original" reference path) is
        the most recent ``periods``-length window of ``returns`` rather than the entire history.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``). Also serves as the
            resampling pool when ``periods`` is narrower than ``returns`` itself.
        sims: Number of simulated paths, including the original (unresampled) path as the first
            column (``sim_0``). Must be at least 1.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        bust: Optional Max Drawdown threshold (e.g. ``-0.2`` for -20%). When given,
            ``bust_probability`` reports the fraction of simulated paths whose max drawdown
            breached it.
        goal: Optional cumulative-return threshold (e.g. ``1.0`` for +100%). When given,
            ``goal_probability`` reports the fraction of simulated paths that reached it.
        confidence: Confidence level for the per-period ``confidence_band``. Defaults to
            ``0.95`` (a 95% band).
        seed: Optional random seed for reproducibility.
        block_size: Optional mean block length (in periods) for a stationary block bootstrap
            (see Note above). Defaults to ``None``, resampling each period independently (i.i.d.).
        periods: Optional simulation horizon in periods, decoupled from ``len(returns)`` (see
            Note above). Defaults to ``None`` (simulate as many periods as ``returns`` contains).

    Returns:
        Dict with keys:

        - ``paths``: DataFrame of cumulative simulated returns, one column per simulation,
                indexed like ``returns``.
        - ``terminal_stats``: Summary statistics (mean, std, min/25%/50%/75%/max) of the final
                cumulative return across simulations.
        - ``max_drawdown_stats``: Same summary statistics for each simulation's Max Drawdown.
        - ``confidence_band``: DataFrame with ``Lower``/``Upper`` columns holding the
                ``confidence``-level percentile range of cumulative return at each period.
        - ``bust_probability``: Fraction of simulations at or below ``bust`` (``None`` if
                ``bust`` wasn't given).
        - ``goal_probability``: Fraction of simulations at or above ``goal`` (``None`` if
                ``goal`` wasn't given).
    """
    series = _simple_returns(returns, return_type)
    if sims < 1:
        raise ValueError("sims must be at least 1")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    if block_size is not None and block_size <= 0:
        raise ValueError("block_size must be positive")

    rng = np.random.default_rng(seed)
    values = series.to_numpy()
    pool_size = len(values)
    horizon = pool_size if periods is None else periods
    if horizon < 1 or horizon > pool_size:
        raise ValueError("periods must be between 1 and len(returns)")

    resampled = np.empty((horizon, sims))
    resampled[:, 0] = values[-horizon:]
    for i in range(1, sims):
        if block_size is None:
            resampled[:, i] = rng.choice(values, size=horizon, replace=True)
        else:
            resampled[:, i] = values[_stationary_bootstrap_indices(rng, pool_size, horizon, block_size)]

    paths = pd.DataFrame(
        np.cumprod(1.0 + resampled, axis=0) - 1.0,
        index=series.index[-horizon:],
        columns=[f"sim_{i}" for i in range(sims)],
    )

    terminal = paths.iloc[-1]
    drawdowns = (1.0 + paths).div((1.0 + paths).cummax()).sub(1.0)
    max_drawdowns = drawdowns.min()

    percentiles = [0.05, 0.25, 0.5, 0.75, 0.95]
    lower_q, upper_q = (1.0 - confidence) / 2.0, 1.0 - (1.0 - confidence) / 2.0
    confidence_band = pd.DataFrame(
        {"Lower": paths.quantile(lower_q, axis=1), "Upper": paths.quantile(upper_q, axis=1)}
    )

    return {
        "paths": paths,
        "terminal_stats": terminal.describe(percentiles=percentiles),
        "max_drawdown_stats": max_drawdowns.describe(percentiles=percentiles),
        "confidence_band": confidence_band,
        "bust_probability": float((max_drawdowns <= bust).mean()) if bust is not None else None,
        "goal_probability": float((terminal >= goal).mean()) if goal is not None else None,
    }


def _future_index(index: pd.Index, periods: int) -> pd.Index:
    """Extrapolate ``periods`` timestamps continuing after a ``DatetimeIndex``.

    Infers a step size from ``index`` (via :func:`pandas.infer_freq`, falling back to the
    median spacing for irregular series) and projects it forward. Returns a plain
    ``RangeIndex`` named ``"trade"`` instead when ``index`` isn't a usable ``DatetimeIndex``
    (fewer than 2 timestamps), since there's no basis to infer a step size.
    """
    if not isinstance(index, pd.DatetimeIndex) or len(index) < 2:
        return pd.RangeIndex(periods, name="trade")
    freq = pd.infer_freq(index)
    if freq is not None:
        return pd.date_range(index[-1], periods=periods + 1, freq=freq)[1:]
    spacing = index.to_series().diff().median()
    return pd.DatetimeIndex([index[-1] + spacing * (i + 1) for i in range(periods)])


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
) -> dict[str, object]:
    """Simulate forward trades with a randomly varied win rate to stress-test a strategy's edge.

    Unlike :func:`montecarlo` (which resamples *periodic* returns to explore plausible
    histories), this simulates forward, trade-by-trade: each simulated path draws ``periods``
    future trades by (1) picking a per-simulation win rate randomly perturbed by up to
    ``win_rate_variance`` from the historical win rate, then (2) for each trade, flipping a coin
    at that win rate and sampling a return with replacement from the historical winning or losing
    trades accordingly. This directly stresses whether a strategy's edge holds up if its win rate
    drifts, rather than just reordering/bootstrapping the exact historical return sequence.

    Note:
        Like the rest of this package, results are expressed as compounded (multiplicative)
        cumulative returns rather than account-currency dollar P&L — pass per-trade *returns* in
        ``trades``, not dollar amounts.

    Note:
        When ``trades`` has a ``DatetimeIndex``, ``paths`` is indexed by ``periods`` timestamps
        extrapolated forward from the last historical trade date (step size inferred via
        :func:`pandas.infer_freq`, falling back to the median spacing for irregular series),
        continuing the timeline where ``real_path`` leaves off, rather than a bare trade count —
        consistent with the date axes used throughout :mod:`qrt.plot`. Falls back to a plain
        ``0..periods - 1`` trade-count index otherwise.

    Args:
        trades: Per-trade return series (simple or log, per ``return_type``) — one entry per
            historical trade, not necessarily a periodic/calendar series, though a
            ``DatetimeIndex`` is used to date the simulated horizon (see Note above) when
            present. Must contain at least one winning and one losing (or breakeven) trade.
        periods: Number of future trades to simulate per path. Must be at least 1.
        sims: Number of simulated paths. Must be at least 1.
        return_type: Whether ``trades`` are ``"simple"`` or ``"log"`` returns.
        win_rate_variance: Amount by which each simulation's win rate is randomly perturbed
            (uniformly, in both directions) from the historical win rate — e.g. ``0.1`` varies a
            55% historical win rate anywhere from 45% to 65% per simulation. Clipped to
            ``[0, 1]``. Defaults to ``0.1``.
        ruin: Max Drawdown threshold (e.g. ``-0.9`` for -90%) below which a path is considered
            "ruined" (having lost most or all of its capital). ``ruin_probability`` reports the
            fraction of paths that breached it. Defaults to ``-0.9``.
        confidence: Confidence level for the per-trade ``confidence_band``. Defaults to ``0.95``.
        seed: Optional random seed for reproducibility.

    Returns:
        Dict with keys:

        - ``paths``: DataFrame of cumulative simulated returns, one column per simulation,
                indexed either by ``periods`` extrapolated future timestamps (when ``trades``
                has a ``DatetimeIndex``) or a plain ``0..periods - 1`` trade count otherwise —
                see the Note above.
        - ``real_path``: Series of the actual historical cumulative compounded return over the
                most recent ``min(periods, len(trades))`` trades, for reference/comparison —
                not part of the simulation. Truncated to ``periods`` (rather than the full
                ``trades`` history) so its scale and length stay comparable to the simulated
                paths, and immediately precedes ``paths`` on the timeline when dated.
        - ``win_rates``: Array of the randomly perturbed win rate used by each simulation.
        - ``terminal_stats``: Summary statistics (mean, std, min/25%/50%/75%/max) of the final
                cumulative return across simulations.
        - ``max_drawdown_stats``: Same summary statistics for each simulation's Max Drawdown.
        - ``confidence_band``: DataFrame with ``Lower``/``Upper`` columns holding the
                ``confidence``-level percentile range of cumulative return at each trade.
        - ``make_money_probability``: Fraction of simulations with a positive terminal return.
        - ``ruin_probability``: Fraction of simulations whose Max Drawdown breached ``ruin``.
        - ``average_profit``/``average_drawdown``: Mean terminal return / mean Max Drawdown
                (signed) across simulations.
        - ``pnldd_ratio``: ``average_profit / abs(average_drawdown)`` — average return earned
                per unit of average drawdown risked.
    """
    series = _simple_returns(trades, return_type, "trades")
    if periods < 1:
        raise ValueError("periods must be at least 1")
    if sims < 1:
        raise ValueError("sims must be at least 1")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    if not 0.0 <= win_rate_variance <= 1.0:
        raise ValueError("win_rate_variance must be between 0 and 1")

    wins = series[series > 0].to_numpy()
    losses = series[series <= 0].to_numpy()
    if not len(wins) or not len(losses):
        raise ValueError("trades must contain both winning and losing trades")

    base_win_rate = len(wins) / len(series)
    rng = np.random.default_rng(seed)

    win_rates = np.clip(base_win_rate + rng.uniform(-win_rate_variance, win_rate_variance, size=sims), 0.0, 1.0)
    is_win = rng.random((periods, sims)) < win_rates
    resampled = np.where(
        is_win,
        rng.choice(wins, size=(periods, sims), replace=True),
        rng.choice(losses, size=(periods, sims), replace=True),
    )

    paths = pd.DataFrame(np.cumprod(1.0 + resampled, axis=0) - 1.0, columns=[f"sim_{i}" for i in range(sims)])
    paths.index = _future_index(series.index, periods)

    recent = series.iloc[-periods:] if periods <= len(series) else series
    real_path = (1.0 + recent).cumprod() - 1.0
    if not isinstance(recent.index, pd.DatetimeIndex):
        real_path.index = pd.RangeIndex(len(recent), name="trade")

    terminal = paths.iloc[-1]
    drawdowns = (1.0 + paths).div((1.0 + paths).cummax()).sub(1.0)
    max_drawdowns = drawdowns.min()

    percentiles = [0.05, 0.25, 0.5, 0.75, 0.95]
    lower_q, upper_q = (1.0 - confidence) / 2.0, 1.0 - (1.0 - confidence) / 2.0
    confidence_band = pd.DataFrame(
        {"Lower": paths.quantile(lower_q, axis=1), "Upper": paths.quantile(upper_q, axis=1)}
    )

    average_profit = float(terminal.mean())
    average_drawdown = float(max_drawdowns.mean())

    return {
        "paths": paths,
        "real_path": real_path,
        "win_rates": win_rates,
        "terminal_stats": terminal.describe(percentiles=percentiles),
        "max_drawdown_stats": max_drawdowns.describe(percentiles=percentiles),
        "confidence_band": confidence_band,
        "make_money_probability": float((terminal > 0).mean()),
        "ruin_probability": float((max_drawdowns <= ruin).mean()),
        "average_profit": average_profit,
        "average_drawdown": average_drawdown,
        "pnldd_ratio": float(average_profit / abs(average_drawdown)) if average_drawdown else float("nan"),
    }


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
) -> dict[str, object]:
    """Simulate noise-perturbed return paths to gauge sensitivity to day-to-day noise/volatility.

    Each simulated path keeps the exact historical sequence of ``returns`` (same order, same
    length, same index) but scales every period's return by ``1 + eps`` where
    ``eps ~ Normal(0, noise)`` — i.e. jitters the *magnitude* of each period's move by a random
    relative fraction without flipping its sign. This asks "would this exact strategy still
    perform similarly if the day-to-day noise/volatility in prices had been slightly different,
    but its underlying trend/edge (the sequence of up/down calls) was unchanged?" — a different
    question from :func:`montecarlo` (which varies the *order*/composition of returns via
    bootstrap resampling) or :func:`variance_test` (which varies the *win rate* itself over a
    forward horizon).

    Note:
        Unlike :func:`montecarlo`, ``noise_test`` never reorders or resamples ``returns`` — every
        simulated path is the same length as ``returns`` and stays aligned to its original index,
        so no separate horizon/resampling-pool decoupling is needed here.

    Args:
        returns: Periodic return series (simple or log, per ``return_type``).
        sims: Number of simulated paths, including the original (unperturbed) path as the first
            column (``sim_0``). Must be at least 1.
        return_type: Whether ``returns`` are ``"simple"`` or ``"log"`` returns.
        noise: Standard deviation of the multiplicative noise applied to each period's return,
            e.g. ``0.1`` randomly scales each return's magnitude by roughly ±10%. Must be
            non-negative.
        bust: Optional Max Drawdown threshold (e.g. ``-0.2`` for -20%). When given,
            ``bust_probability`` reports the fraction of simulated paths whose max drawdown
            breached it.
        goal: Optional cumulative-return threshold (e.g. ``1.0`` for +100%). When given,
            ``goal_probability`` reports the fraction of simulated paths that reached it.
        confidence: Confidence level for the per-period ``confidence_band``. Defaults to
            ``0.95`` (a 95% band).
        seed: Optional random seed for reproducibility.

    Returns:
        Dict with keys:

        - ``paths``: DataFrame of cumulative simulated returns, one column per simulation
                (``sim_0`` is the original, unperturbed path), indexed like ``returns``.
        - ``terminal_stats``: Summary statistics (mean, std, min/25%/50%/75%/max) of the final
                cumulative return across simulations.
        - ``max_drawdown_stats``: Same summary statistics for each simulation's Max Drawdown.
        - ``confidence_band``: DataFrame with ``Lower``/``Upper`` columns holding the
                ``confidence``-level percentile range of cumulative return at each period.
        - ``bust_probability``: Fraction of simulations at or below ``bust`` (``None`` if
                ``bust`` wasn't given).
        - ``goal_probability``: Fraction of simulations at or above ``goal`` (``None`` if
                ``goal`` wasn't given).
    """
    series = _simple_returns(returns, return_type)
    if sims < 1:
        raise ValueError("sims must be at least 1")
    if noise < 0.0:
        raise ValueError("noise must be non-negative")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")

    rng = np.random.default_rng(seed)
    values = series.to_numpy()
    n = len(values)

    eps = np.zeros((n, sims))
    if noise > 0.0 and sims > 1:
        eps[:, 1:] = rng.normal(0.0, noise, size=(n, sims - 1))
    noisy = values[:, None] * (1.0 + eps)
    noisy[:, 0] = values

    paths = pd.DataFrame(
        np.cumprod(1.0 + noisy, axis=0) - 1.0,
        index=series.index,
        columns=[f"sim_{i}" for i in range(sims)],
    )

    terminal = paths.iloc[-1]
    drawdowns = (1.0 + paths).div((1.0 + paths).cummax()).sub(1.0)
    max_drawdowns = drawdowns.min()

    percentiles = [0.05, 0.25, 0.5, 0.75, 0.95]
    lower_q, upper_q = (1.0 - confidence) / 2.0, 1.0 - (1.0 - confidence) / 2.0
    confidence_band = pd.DataFrame(
        {"Lower": paths.quantile(lower_q, axis=1), "Upper": paths.quantile(upper_q, axis=1)}
    )

    return {
        "paths": paths,
        "terminal_stats": terminal.describe(percentiles=percentiles),
        "max_drawdown_stats": max_drawdowns.describe(percentiles=percentiles),
        "confidence_band": confidence_band,
        "bust_probability": float((max_drawdowns <= bust).mean()) if bust is not None else None,
        "goal_probability": float((terminal >= goal).mean()) if goal is not None else None,
    }


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
        rf: float = 0.0,
    ) -> None:
        self.returns = _simple_returns(data, return_type)
        self.benchmark = _simple_returns(benchmark, return_type, "Benchmark") if benchmark is not None else None
        self.periods_per_year = periods_per_year
        self.rf = rf

    def _require_benchmark(self) -> pd.Series:
        if self.benchmark is None:
            raise ValueError("This stat requires a benchmark; pass benchmark=... to qrt.stats.returns(...)")
        return self.benchmark

    def performance(self) -> pd.Series:
        """See :func:`performance`."""
        return performance(self.returns, periods_per_year=self.periods_per_year, rf=self.rf)

    def metrics(self, mode: Literal["basic", "full"] = "full") -> pd.DataFrame:
        """See :func:`metrics`."""
        return metrics(self.returns, self.benchmark, mode=mode, periods_per_year=self.periods_per_year, rf=self.rf)

    def period_returns(self) -> pd.Series:
        """See :func:`period_returns`."""
        return period_returns(self.returns, periods_per_year=self.periods_per_year)

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
        return rolling_sharpe(self.returns, window, periods_per_year=self.periods_per_year, rf=self.rf)

    def rolling_sortino(self, window: int = 63) -> pd.Series:
        """See :func:`rolling_sortino`."""
        return rolling_sortino(self.returns, window, periods_per_year=self.periods_per_year, rf=self.rf)

    def rolling_volatility(self, window: int = 63) -> pd.Series:
        """See :func:`rolling_volatility`."""
        return rolling_volatility(self.returns, window, periods_per_year=self.periods_per_year)

    def monthly_returns(self, *, eoy: bool = True) -> pd.DataFrame:
        """See :func:`monthly_returns`."""
        return monthly_returns(self.returns, eoy=eoy)

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
    rf: float = 0.0,
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
        rf: Annualized risk-free rate, used by ``.performance()`` and
            ``.rolling_sharpe()``. Defaults to ``0.0``.

    Returns:
        A :class:`Returns` object exposing bound stats (``.performance()``,
        ``.alpha()``, ``.beta()``, ``.rolling_beta()``, ...) and ``.plot(kind=...)``.
    """
    return Returns(data, benchmark, return_type=return_type, periods_per_year=periods_per_year, rf=rf)


# ---------------------------------------------------------------------------
# Trades format (one row per round-trip trade)
# ---------------------------------------------------------------------------

#: Reserved columns of the canonical trades format, in order. Any further
#: columns on a trades frame are entry-time feature snapshots (free-form
#: trade metadata, surfaced in plot hovers and usable as `trade_stats` groupers).
TRADE_COLUMNS = (
    "symbol",
    "entry_time",
    "exit_time",
    "direction",
    "entry_reason",
    "exit_reason",
    "entry_price",
    "exit_price",
    "return",
    "mae",
    "mfe",
    "size",
    "fees",
)

#: Valid ``direction`` values for the canonical trades format:
#: ``1`` = long, ``-1`` = short.
_DIRECTION_VALUES = frozenset({1, -1})


def _validate_trades(trades: pd.DataFrame, required: tuple[str, ...]) -> pd.DataFrame:
    """Check the trades frame has the required canonical columns."""
    missing = [column for column in required if column not in trades.columns]
    if missing:
        raise ValueError(
            f"trades is missing required column(s) {missing}; expected the "
            "canonical trades format (see qrt.data.datasets.TRADE_LOGS demos)"
        )
    unknown = set(trades["direction"]) - _DIRECTION_VALUES
    if "direction" in required and unknown:
        raise ValueError(
            f"Unknown direction value(s) {sorted(unknown)}; expected 1 (long) / -1 (short)"
        )
    return trades


def trades_to_returns(trades: pd.DataFrame, prices: pd.Series | None = None) -> pd.Series:
    """Convert a trade log into a periodic return stream.

    The bridge from qrt's canonical trades format (one row per round-trip
    trade, see :mod:`qrt.data.datasets`) to the return-stream form every
    other :mod:`qrt.stats`/:mod:`qrt.plot` function consumes.

    Without ``prices``, each trade's whole return is attributed at its
    ``exit_time`` (compounded when several trades exit on the same bar) --
    fine for aggregate stats, but intra-trade drawdown and volatility are
    invisible. With ``prices`` (a close series covering the trade span),
    trades are marked to market: each bar in a trade contributes its
    close-to-close return (entry bar: close vs ``entry_price``; exit bar:
    ``exit_price`` vs previous close), direction-adjusted, and bars with no
    open trade contribute ``0.0`` -- giving honest drawdown/volatility/
    exposure statistics.

    Note:
        For long trades, marked-to-market bar returns compound exactly to
        the trade's stored ``return``. For shorts they model a *daily
        rebalanced* short position, which compounds slightly differently
        than the unrebalanced trade-level return -- both are correct, they
        answer different questions.

    Args:
        trades: Canonical trades-format DataFrame.
        prices: Optional close series with a ``DatetimeIndex`` covering the
            trade span (e.g. ``q.data.datasets.load("spy")["close"]``).

    Returns:
        Periodic simple-return series named ``"return"``, indexed by
        ``exit_time`` (without ``prices``) or by the full ``prices`` index
        (with ``prices``).
    """
    _validate_trades(trades, ("entry_time", "exit_time", "direction", "return"))
    if prices is None:
        out = (
            trades.groupby("exit_time")["return"]
            .apply(lambda group: (1.0 + group).prod() - 1.0)
            .sort_index()
        )
        return out.rename("return")

    compounded = pd.Series(1.0, index=prices.index, name="return")
    for trade in trades.to_dict("records"):  # not itertuples: it mangles the 'return' column (keyword)
        sign = trade["direction"]
        window = prices.loc[trade["entry_time"] : trade["exit_time"]]
        if window.empty:  # trade span not covered by prices: attribute at exit
            bar_returns = pd.Series([trade["return"]], index=[trade["exit_time"]], dtype=float)
        else:
            marks = window.copy()
            marks.iloc[-1] = trade["exit_price"]
            bar_returns = marks.pct_change()
            bar_returns.iloc[0] = marks.iloc[0] / trade["entry_price"] - 1.0
        compounded = compounded.mul(1.0 + sign * bar_returns, fill_value=1.0)
    return compounded.sub(1.0).rename("return")


def trades_to_positions(trades: pd.DataFrame, index: pd.Index) -> pd.Series:
    """Convert a trade log into a signed position series over ``index``.

    Each trade contributes ``+1`` (long) or ``-1`` (short) on every bar from
    its ``entry_time`` through its ``exit_time`` (inclusive); overlapping
    trades sum. Bars with no open trade are ``0`` -- the basis for exposure
    timelines and time-in-market analysis.

    Args:
        trades: Canonical trades-format DataFrame.
        index: Target index (e.g. ``prices.index``) to evaluate positions on.

    Returns:
        Integer position series named ``"position"`` over ``index``.
    """
    _validate_trades(trades, ("entry_time", "exit_time", "direction"))
    positions = pd.Series(0, index=index, name="position")
    for trade in trades.to_dict("records"):
        positions.loc[trade["entry_time"] : trade["exit_time"]] += trade["direction"]
    return positions


def _merged_interval_days(trades: pd.DataFrame) -> float:
    """Total days covered by the union of [entry_time, exit_time] intervals."""
    intervals = trades[["entry_time", "exit_time"]].sort_values("entry_time")
    total = pd.Timedelta(0)
    current_start = current_end = None
    for start, end in intervals.itertuples(index=False):
        if current_end is None or start > current_end:
            if current_end is not None:
                total += current_end - current_start
            current_start, current_end = start, end
        else:
            current_end = max(current_end, end)
    if current_end is not None:
        total += current_end - current_start
    return total / pd.Timedelta(days=1)


def _trade_group_stats(trades: pd.DataFrame) -> pd.Series:
    """Compute the trade-level metric block for one group of trades."""
    trade_returns = trades["return"]
    wins = trade_returns[trade_returns > 0]
    losses = trade_returns[trade_returns < 0]
    durations = (trades["exit_time"] - trades["entry_time"]) / pd.Timedelta(days=1)
    span_days = (trades["exit_time"].max() - trades["entry_time"].min()) / pd.Timedelta(days=1)
    avg_win_value = wins.mean() if len(wins) else float("nan")
    avg_loss_value = losses.mean() if len(losses) else float("nan")
    gross_losses = abs(losses.sum())
    return pd.Series(
        {
            "Trades": float(len(trades)),
            "Win Rate": len(wins) / len(trade_returns[trade_returns != 0]) if (trade_returns != 0).any() else float("nan"),
            "Total Return": (1.0 + trade_returns).prod() - 1.0,
            "Avg Return": trade_returns.mean(),
            "Avg Win": avg_win_value,
            "Avg Loss": avg_loss_value,
            "Payoff Ratio": avg_win_value / abs(avg_loss_value) if losses.any() else float("nan"),
            "Profit Factor": wins.sum() / gross_losses if gross_losses else float("nan"),
            "Best": trade_returns.max(),
            "Worst": trade_returns.min(),
            "Avg MAE": trades["mae"].mean() if "mae" in trades else float("nan"),
            "Avg MFE": trades["mfe"].mean() if "mfe" in trades else float("nan"),
            "Avg Days": durations.mean(),
            "Median Days": durations.median(),
            "Exposure": _merged_interval_days(trades) / span_days if span_days else float("nan"),
        },
        dtype=float,
    )


def trade_stats(trades: pd.DataFrame, by: str | None = None) -> pd.DataFrame:
    """Calculate trade-level statistics from a canonical trades-format log.

    Unlike the return-stream metrics (:func:`performance`, :func:`win_rate`,
    ...), these operate on whole round-trip trades -- so ``Win Rate`` is the
    share of winning *trades*, ``Avg Days`` the mean holding period, and
    ``Exposure`` the fraction of calendar time (first entry to last exit)
    with an open position, computed from the union of actual trade spans.

    Args:
        trades: Canonical trades-format DataFrame (see :mod:`qrt.data.datasets`).
        by: Optional column to group by (e.g. ``"exit_reason"``,
            ``"direction"``, or any feature-snapshot column). When given, the
            result has one column per group next to the ``All`` column.

    Returns:
        DataFrame of metrics (rows) by group (columns):

        - ``Trades``: Number of round-trip trades.
        - ``Win Rate``: Share of non-zero-return trades that were profitable.
        - ``Total Return``: Compounded return across the group's trades.
        - ``Avg Return`` / ``Avg Win`` / ``Avg Loss``: Mean trade returns
                (overall, winners only, losers only).
        - ``Payoff Ratio``: Avg Win / \\|Avg Loss\\|.
        - ``Profit Factor``: Gross wins / gross losses.
        - ``Best`` / ``Worst``: Extreme single-trade returns.
        - ``Avg MAE`` / ``Avg MFE``: Mean max adverse/favorable excursion
                (``NaN`` when the columns are absent).
        - ``Avg Days`` / ``Median Days``: Holding period in calendar days.
        - ``Exposure``: Fraction of the group's calendar span with an open
                position.

    Raises:
        ValueError: If ``trades`` lacks canonical columns, or ``by`` is not a column.
    """
    _validate_trades(trades, ("entry_time", "exit_time", "direction", "return"))
    if len(trades) == 0:
        raise ValueError("trades is empty")
    result = {"All": _trade_group_stats(trades)}
    if by is not None:
        if by not in trades.columns:
            raise ValueError(f"by={by!r} is not a trades column. Available: {list(trades.columns)}")
        for value, group in trades.groupby(by, observed=True):
            result[str(value)] = _trade_group_stats(group)
    return pd.DataFrame(result)
