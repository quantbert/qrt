"""Shared validation and normalization for return-series statistics."""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

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