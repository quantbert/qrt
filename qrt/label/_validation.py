"""Shared validation helpers for labeling operations."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import numpy as np
import pandas as pd


def numeric_series(
    series: pd.Series,
    name: str,
    *,
    allow_missing: bool = False,
    positive: bool = False,
) -> pd.Series:
    if not isinstance(series, pd.Series):
        raise TypeError(f"{name} must be a pandas Series")
    if pd.api.types.is_bool_dtype(series) or not pd.api.types.is_numeric_dtype(series):
        raise TypeError(f"{name} must contain numeric values")
    validate_index(series.index, f"{name} index")

    values = series.astype(float)
    if not allow_missing and values.isna().any():
        raise ValueError(f"{name} must not contain missing values")
    finite_values = values.dropna().to_numpy()
    if not np.isfinite(finite_values).all():
        raise ValueError(f"{name} must contain only finite values")
    if positive and (finite_values <= 0).any():
        raise ValueError(f"{name} must contain only positive values")
    return values


def validate_index(index: pd.Index, name: str = "index") -> None:
    if not isinstance(index, pd.Index):
        raise TypeError(f"{name} must be a pandas Index")
    if index.has_duplicates:
        raise ValueError(f"{name} must not contain duplicates")
    if not index.is_monotonic_increasing:
        raise ValueError(f"{name} must be sorted in increasing order")


def event_index(
    events: pd.Index | Iterable[Any] | None,
    observations: pd.Index,
) -> pd.Index:
    if events is None:
        return observations.copy()
    if isinstance(events, (str, bytes)):
        raise TypeError("events must be an index or iterable of index labels")

    result = events.copy() if isinstance(events, pd.Index) else pd.Index(events)
    validate_index(result, "events")
    if not result.isin(observations).all():
        raise ValueError("every event must be present in the observations index")
    return result.rename(observations.name)


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


def non_negative_number(value: float, name: str) -> float:
    result = finite_number(value, name)
    if result < 0:
        raise ValueError(f"{name} must be non-negative and finite")
    return result


def positive_number(value: float, name: str) -> float:
    result = non_negative_number(value, name)
    if result == 0:
        raise ValueError(f"{name} must be positive")
    return result


def aligned_numeric_values(
    value: float | pd.Series,
    events: pd.Index,
    name: str,
    *,
    allow_missing: bool = False,
    positive: bool = False,
    non_negative: bool = False,
) -> pd.Series:
    if positive and non_negative:
        raise ValueError("positive and non_negative cannot both be requested")

    if isinstance(value, pd.Series):
        result = numeric_series(
            value,
            name,
            allow_missing=allow_missing,
        )
        if not events.isin(result.index).all():
            raise ValueError(f"{name} must contain every event")
        result = result.reindex(events)
    else:
        number = (
            non_negative_number(value, name)
            if non_negative
            else finite_number(value, name)
        )
        result = pd.Series(number, index=events, dtype=float, name=name)

    finite = result.dropna()
    if positive and (finite <= 0).any():
        raise ValueError(f"{name} must contain only positive values")
    if non_negative and (finite < 0).any():
        raise ValueError(f"{name} must contain only non-negative values")
    if not allow_missing and result.isna().any():
        raise ValueError(f"{name} must not contain missing values")
    return result.astype(float).rename(name)