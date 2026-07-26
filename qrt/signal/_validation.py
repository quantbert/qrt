"""Validation for point-in-time signal objects."""

from __future__ import annotations

from numbers import Integral

import numpy as np
import pandas as pd

SignalLike = pd.Series | pd.DataFrame


def as_signal(values: SignalLike) -> SignalLike:
    """Validate and copy a canonical QRT signal object.

    A Series represents one asset through time. A DataFrame represents a
    time-by-asset panel. Both forms require an ordered, unique index, numeric
    values, and finite non-missing observations.
    """
    if not isinstance(values, (pd.Series, pd.DataFrame)):
        raise TypeError("values must be a pandas Series or DataFrame")
    if values.empty:
        raise ValueError("values must not be empty")
    if not values.index.is_unique:
        raise ValueError("values index must not contain duplicates")
    if not values.index.is_monotonic_increasing:
        raise ValueError("values index must be sorted in increasing order")
    if values.index.hasnans:
        raise ValueError("values index must not contain missing values")
    if isinstance(values, pd.Series):
        if pd.api.types.is_bool_dtype(values) or not pd.api.types.is_numeric_dtype(values):
            raise TypeError("values must be numeric")
    else:
        if values.shape[1] == 0:
            raise ValueError("values must contain at least one asset column")
        if not values.columns.is_unique:
            raise ValueError("values columns must not contain duplicates")
        if any(
            pd.api.types.is_bool_dtype(values[column])
            or not pd.api.types.is_numeric_dtype(values[column])
            for column in values
        ):
            raise TypeError("values must be numeric")
    array = values.to_numpy(dtype=float)
    if not np.isfinite(array[~np.isnan(array)]).all():
        raise ValueError("values must contain only finite values")
    return values.astype(float).copy()


def finite_number(value: float, name: str) -> float:
    if isinstance(value, bool) or not np.isscalar(value):
        raise TypeError(f"{name} must be a number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} must be a number") from exc
    if not np.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def positive_number(value: float, name: str) -> float:
    result = finite_number(value, name)
    if result <= 0:
        raise ValueError(f"{name} must be positive")
    return result


def non_negative_integer(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return int(value)


def directional(values: SignalLike) -> SignalLike:
    signal = as_signal(values)
    observed = signal.to_numpy(dtype=float)
    observed = observed[~np.isnan(observed)]
    if not np.isin(observed, (-1.0, 0.0, 1.0)).all():
        raise ValueError("values must contain only -1, 0, 1, or missing values")
    return signal