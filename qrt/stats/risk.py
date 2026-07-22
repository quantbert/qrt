"""Downside and tail-risk estimators expressed as non-negative losses."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.special import logsumexp
from scipy.stats import norm

from qrt.stats._returns import ReturnType, _simple_returns


def _confidence(confidence: float) -> float:
    if isinstance(confidence, bool) or not np.isscalar(confidence):
        raise TypeError("confidence must be a scalar")
    value = float(confidence)
    if not np.isfinite(value) or not 0.0 < value < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    return value


def _losses(returns: pd.Series, return_type: ReturnType) -> np.ndarray:
    series = _simple_returns(returns, return_type)
    return -series.to_numpy(dtype=float)


def historical_value_at_risk(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    confidence: float = 0.95,
) -> float:
    """Calculate historical Value at Risk as a non-negative loss magnitude."""
    level = _confidence(confidence)
    loss = float(np.quantile(_losses(returns, return_type), level))
    return max(0.0, loss)


def historical_expected_shortfall(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    confidence: float = 0.95,
) -> float:
    """Average the worst ``1 - confidence`` loss mass.

    A fractional boundary observation is included when the requested tail
    mass is not an integer number of observations.
    """
    level = _confidence(confidence)
    losses = np.sort(_losses(returns, return_type))[::-1]
    tail_mass = (1.0 - level) * len(losses)
    full_count = int(np.floor(tail_mass))
    fraction = tail_mass - full_count
    total = float(losses[:full_count].sum())
    if fraction > 0.0:
        total += fraction * float(losses[full_count])
    return max(0.0, total / tail_mass)


def gaussian_value_at_risk(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    confidence: float = 0.95,
) -> float:
    """Calculate Gaussian Value at Risk as a non-negative loss magnitude."""
    level = _confidence(confidence)
    series = _simple_returns(returns, return_type)
    loss_mean = -float(series.mean())
    loss_std = float(series.std(ddof=1)) if len(series) > 1 else 0.0
    return max(0.0, loss_mean + loss_std * float(norm.ppf(level)))


def gaussian_expected_shortfall(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    confidence: float = 0.95,
) -> float:
    """Calculate closed-form Gaussian Expected Shortfall as a loss magnitude."""
    level = _confidence(confidence)
    series = _simple_returns(returns, return_type)
    loss_mean = -float(series.mean())
    loss_std = float(series.std(ddof=1)) if len(series) > 1 else 0.0
    quantile = float(norm.ppf(level))
    result = loss_mean + loss_std * float(norm.pdf(quantile)) / (1.0 - level)
    return max(0.0, result)


def tail_conditional_expectation(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    confidence: float = 0.95,
) -> float:
    """Return the mean observed loss at or beyond historical VaR."""
    level = _confidence(confidence)
    losses = _losses(returns, return_type)
    threshold = float(np.quantile(losses, level))
    return max(0.0, float(losses[losses >= threshold].mean()))


def entropic_value_at_risk(
    returns: pd.Series,
    *,
    return_type: ReturnType = "simple",
    confidence: float = 0.95,
) -> float:
    r"""Calculate EVaR by minimizing its entropic upper bound.

    For losses $L$ and confidence $c$, EVaR is
    $\inf_{z>0}(\log E[e^{zL}] - \log(1-c)) / z$.
    """
    level = _confidence(confidence)
    losses = _losses(returns, return_type)
    scale = max(float(np.std(losses)), float(np.max(np.abs(losses))), 1e-12)
    if np.ptp(losses) <= np.finfo(float).eps * scale:
        return max(0.0, float(losses[0]))
    log_tail_probability = np.log1p(-level)
    count = len(losses)

    def objective(z: float) -> float:
        log_mgf = float(logsumexp(z * losses) - np.log(count))
        return (log_mgf - log_tail_probability) / z

    result = minimize_scalar(
        objective,
        bounds=(1e-8 / scale, 1e4 / scale),
        method="bounded",
        options={"xatol": 1e-10 / scale},
    )
    if not result.success or not np.isfinite(result.fun):
        raise RuntimeError("EVaR optimization did not converge")
    return max(0.0, float(result.fun))


def maximum_observed_dollar_loss(
    returns: pd.Series,
    *,
    notional: float,
    return_type: ReturnType = "simple",
) -> float:
    """Scale the largest observed one-period loss by a positive notional."""
    if isinstance(notional, bool) or not np.isscalar(notional):
        raise TypeError("notional must be a scalar")
    notional_value = float(notional)
    if not np.isfinite(notional_value) or notional_value <= 0.0:
        raise ValueError("notional must be positive")
    worst_loss = max(0.0, float(np.max(_losses(returns, return_type))))
    return notional_value * worst_loss


def lower_partial_moment(
    returns: pd.Series,
    *,
    threshold: float = 0.0,
    order: float = 1.0,
    return_type: ReturnType = "simple",
) -> float:
    r"""Calculate $E[\max(threshold - return, 0)^{order}]$."""
    if isinstance(threshold, bool) or not np.isscalar(threshold):
        raise TypeError("threshold must be a scalar")
    if isinstance(order, bool) or not np.isscalar(order):
        raise TypeError("order must be a scalar")
    threshold_value = float(threshold)
    order_value = float(order)
    if not np.isfinite(threshold_value):
        raise ValueError("threshold must be finite")
    if not np.isfinite(order_value) or order_value < 0.0:
        raise ValueError("order must be non-negative")
    series = _simple_returns(returns, return_type)
    shortfall = np.maximum(threshold_value - series.to_numpy(dtype=float), 0.0)
    if order_value == 0.0:
        return float(np.mean(shortfall > 0.0))
    return float(np.mean(shortfall**order_value))


__all__ = [
    "entropic_value_at_risk",
    "gaussian_expected_shortfall",
    "gaussian_value_at_risk",
    "historical_expected_shortfall",
    "historical_value_at_risk",
    "lower_partial_moment",
    "maximum_observed_dollar_loss",
    "tail_conditional_expectation",
]