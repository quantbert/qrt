"""Historical and entropic downside-risk measures."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.special import logsumexp


def _returns(returns: pd.Series) -> pd.Series:
    if not isinstance(returns, pd.Series):
        raise TypeError("returns must be a pandas Series")
    if not pd.api.types.is_numeric_dtype(returns):
        raise TypeError("returns must be numeric")
    values = returns.dropna().astype(float)
    if values.empty:
        raise ValueError("returns must contain at least one observation")
    if not np.isfinite(values.to_numpy()).all():
        raise ValueError("returns must contain only finite values")
    return values


def _confidence(confidence: float) -> float:
    if isinstance(confidence, bool) or not np.isscalar(confidence):
        raise TypeError("confidence must be a scalar")
    value = float(confidence)
    if not np.isfinite(value) or not 0.0 < value < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    return value


def _losses(returns: pd.Series) -> np.ndarray:
    return -_returns(returns).to_numpy(dtype=float)


def value_at_risk(returns: pd.Series, *, confidence: float = 0.95) -> float:
    """Calculate historical Value at Risk as a positive loss magnitude."""
    level = _confidence(confidence)
    loss = float(np.quantile(_losses(returns), level))
    return max(0.0, loss)


def conditional_value_at_risk(
    returns: pd.Series, *, confidence: float = 0.95
) -> float:
    """Calculate historical CVaR from the worst ``1 - confidence`` tail.

    A fractional boundary observation is included when the requested tail mass
    is not an integer number of observations.
    """
    level = _confidence(confidence)
    losses = np.sort(_losses(returns))[::-1]
    tail_mass = (1.0 - level) * len(losses)
    full_count = int(np.floor(tail_mass))
    fraction = tail_mass - full_count
    total = float(losses[:full_count].sum())
    if fraction > 0.0:
        total += fraction * float(losses[full_count])
    result = total / tail_mass
    return max(0.0, result)


def tail_conditional_expectation(
    returns: pd.Series, *, confidence: float = 0.95
) -> float:
    """Return the mean observed loss at or beyond historical VaR."""
    level = _confidence(confidence)
    losses = _losses(returns)
    threshold = float(np.quantile(losses, level))
    tail = losses[losses >= threshold]
    return max(0.0, float(tail.mean()))


def entropic_value_at_risk(
    returns: pd.Series, *, confidence: float = 0.95
) -> float:
    r"""Calculate EVaR by minimizing its entropic upper bound.

    For losses $L$ and confidence $c$, EVaR is
    $\inf_{z>0}(\log E[e^{zL}] - \log(1-c)) / z$.
    """
    level = _confidence(confidence)
    losses = _losses(returns)
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


def worst_case_dollar_risk(
    returns: pd.Series,
    *,
    notional: float = 1.0,
) -> float:
    """Scale the worst observed one-period loss by a positive notional."""
    if isinstance(notional, bool) or not np.isscalar(notional):
        raise TypeError("notional must be a scalar")
    notional_value = float(notional)
    if not np.isfinite(notional_value) or notional_value <= 0.0:
        raise ValueError("notional must be positive")
    worst_loss = max(0.0, float(np.max(_losses(returns))))
    return notional_value * worst_loss


def lower_partial_moment(
    returns: pd.Series,
    *,
    threshold: float = 0.0,
    order: float = 1.0,
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
    shortfall = np.maximum(
        threshold_value - _returns(returns).to_numpy(dtype=float), 0.0
    )
    if order_value == 0.0:
        return float(np.mean(shortfall > 0.0))
    return float(np.mean(shortfall**order_value))


var = value_at_risk
cvar = conditional_value_at_risk
evar = entropic_value_at_risk
tce = tail_conditional_expectation
wcdr = worst_case_dollar_risk
lpm = lower_partial_moment