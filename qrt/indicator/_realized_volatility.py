"""Intraday realized-volatility estimators."""

from collections.abc import Callable

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike


def _as_returns(values: ArrayLike, minimum: int, estimator: str) -> np.ndarray:
    returns = np.asarray(values, dtype=float)
    if returns.ndim != 1:
        raise ValueError("returns must be one-dimensional")
    if len(returns) < minimum:
        raise ValueError(f"{estimator} requires at least {minimum} returns")
    if not np.isfinite(returns).all():
        raise ValueError("returns must contain only finite values")
    return returns


def log_returns(prices: ArrayLike) -> np.ndarray:
    """Calculate consecutive logarithmic returns from positive prices."""
    values = np.asarray(prices, dtype=float)
    if values.ndim != 1:
        raise ValueError("prices must be one-dimensional")
    if len(values) < 2:
        raise ValueError("log_returns requires at least 2 prices")
    if not np.isfinite(values).all():
        raise ValueError("prices must contain only finite values")
    if (values <= 0).any():
        raise ValueError("prices must be strictly positive")
    return np.diff(np.log(values))


def realized_variance(returns: ArrayLike) -> float:
    """Calculate realized variance as the sum of squared returns."""
    values = _as_returns(returns, 1, "realized_variance")
    return float(np.sum(values**2))


def realized_quarticity(returns: ArrayLike) -> float:
    """Calculate realized quarticity."""
    values = _as_returns(returns, 1, "realized_quarticity")
    return float((len(values) / 3) * np.sum(values**4))


def bipower_variation(returns: ArrayLike) -> float:
    """Calculate finite-sample-adjusted realized bipower variation."""
    values = _as_returns(returns, 2, "bipower_variation")
    adjustment = len(values) / (len(values) - 1)
    products = np.abs(values[1:]) * np.abs(values[:-1])
    return float((np.pi / 2) * adjustment * np.sum(products))


def med_rv(returns: ArrayLike) -> float:
    """Calculate the median realized-volatility estimator."""
    values = np.abs(_as_returns(returns, 3, "med_rv"))
    adjustment = len(values) / (len(values) - 2)
    constant = np.pi / (6 - 4 * np.sqrt(3) + np.pi)
    medians = np.median(
        np.stack([values[:-2], values[1:-1], values[2:]]), axis=0
    )
    return float(constant * adjustment * np.sum(medians**2))


def min_rv(returns: ArrayLike) -> float:
    """Calculate the minimum realized-volatility estimator."""
    values = np.abs(_as_returns(returns, 2, "min_rv"))
    adjustment = len(values) / (len(values) - 1)
    constant = np.pi / (np.pi - 2)
    minima = np.minimum(values[:-1], values[1:])
    return float(constant * adjustment * np.sum(minima**2))


_ESTIMATORS: dict[str, Callable[[ArrayLike], float]] = {
    "realized_variance": realized_variance,
    "realized_quarticity": realized_quarticity,
    "bipower_variation": bipower_variation,
    "med_rv": med_rv,
    "min_rv": min_rv,
}


def realized_volatility(
    data: pd.DataFrame,
    *,
    time_col: str = "time",
    price_col: str = "price",
    session_col: str = "session",
) -> pd.DataFrame:
    """Calculate realized-volatility measures for each intraday session.

    Args:
        data: Intraday observations for one instrument.
        time_col: Observation timestamp column.
        price_col: Positive trade or sampled-price column.
        session_col: Explicit session label column.

    Returns:
        DataFrame indexed by session with one column per estimator.

    Raises:
        ValueError: If required data is missing or a session has fewer than four
            prices (three returns).
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame")
    required = [time_col, price_col, session_col]
    missing = [column for column in required if column not in data]
    if missing:
        raise ValueError(f"data is missing required columns: {missing}")
    if "symbol" in data and data["symbol"].nunique(dropna=False) > 1:
        raise ValueError("data must contain observations for one symbol")
    if data[required].isna().any().any():
        raise ValueError("time, price, and session values must not be missing")

    frame = data.loc[:, required].copy()
    frame[time_col] = pd.to_datetime(frame[time_col], errors="raise")
    frame = frame.sort_values([session_col, time_col], kind="stable")

    rows = []
    sessions = []
    for session, group in frame.groupby(session_col, sort=True, observed=True):
        if len(group) < 4:
            raise ValueError(f"session {session!r} requires at least 4 prices")
        returns = log_returns(group[price_col].to_numpy())
        rows.append({name: estimator(returns) for name, estimator in _ESTIMATORS.items()})
        sessions.append(session)

    result = pd.DataFrame(rows, index=pd.Index(sessions, name=session_col))
    return result.loc[:, list(_ESTIMATORS)]