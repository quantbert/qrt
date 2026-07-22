"""Label-preserving transforms across an asset universe."""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

RankMethod = Literal["average", "min", "max", "first", "dense"]
Values = pd.Series | pd.DataFrame


def _numeric_values(values: Values) -> Values:
    if not isinstance(values, (pd.Series, pd.DataFrame)):
        raise TypeError("values must be a pandas Series or DataFrame")
    if isinstance(values, pd.Series):
        if not pd.api.types.is_numeric_dtype(values):
            raise TypeError("values must be numeric")
    elif any(not pd.api.types.is_numeric_dtype(values[column]) for column in values):
        raise TypeError("values must be numeric")
    array = values.to_numpy(dtype=float)
    if not np.isfinite(array[~np.isnan(array)]).all():
        raise ValueError("values must contain only finite values")
    return values.astype(float).copy()


def rank(
    values: Values,
    *,
    axis: int | Literal["index", "columns"] = "columns",
    method: RankMethod = "average",
    ascending: bool = True,
    na_option: Literal["keep", "top", "bottom"] = "keep",
) -> Values:
    """Rank assets within a snapshot or each row of a time-by-asset panel."""
    numeric = _numeric_values(values)
    if isinstance(numeric, pd.Series):
        return numeric.rank(method=method, ascending=ascending, na_option=na_option)
    return numeric.rank(
        axis=axis, method=method, ascending=ascending, na_option=na_option
    )


def percentile_rank(
    values: Values,
    *,
    axis: int | Literal["index", "columns"] = "columns",
    method: RankMethod = "average",
    ascending: bool = True,
) -> Values:
    """Return cross-sectional ranks scaled to the interval ``(0, 1]``."""
    numeric = _numeric_values(values)
    if isinstance(numeric, pd.Series):
        return numeric.rank(method=method, ascending=ascending, pct=True)
    return numeric.rank(axis=axis, method=method, ascending=ascending, pct=True)


def zscore(
    values: Values,
    *,
    axis: int | Literal["index", "columns"] = "columns",
    ddof: int = 0,
) -> Values:
    """Standardize values against their cross-sectional mean and deviation."""
    if isinstance(ddof, bool) or not isinstance(ddof, int) or ddof < 0:
        raise ValueError("ddof must be a non-negative integer")
    numeric = _numeric_values(values)
    if isinstance(numeric, pd.Series):
        return (numeric - numeric.mean()) / numeric.std(ddof=ddof)
    means = numeric.mean(axis=axis)
    deviations = numeric.std(axis=axis, ddof=ddof)
    if axis in (1, "columns"):
        return numeric.sub(means, axis="index").div(deviations, axis="index")
    return numeric.sub(means, axis="columns").div(deviations, axis="columns")


def neutralize(
    values: pd.Series,
    exposures: pd.Series | pd.DataFrame,
    *,
    weights: pd.Series | None = None,
    add_intercept: bool = True,
) -> pd.Series:
    """Return weighted least-squares residuals after removing exposures.

    Numeric exposures are used directly. Categorical exposures are expanded
    into dummy variables, making sector or industry neutralization explicit.
    Rows containing missing values remain missing in the returned Series.
    """
    if not isinstance(values, pd.Series):
        raise TypeError("values must be a pandas Series")
    if not isinstance(exposures, (pd.Series, pd.DataFrame)):
        raise TypeError("exposures must be a pandas Series or DataFrame")
    frame = exposures.to_frame() if isinstance(exposures, pd.Series) else exposures.copy()
    if not values.index.equals(frame.index):
        raise ValueError("values and exposures must have exactly the same index")
    if frame.shape[1] == 0:
        raise ValueError("exposures must contain at least one column")
    if weights is not None:
        if not isinstance(weights, pd.Series):
            raise TypeError("weights must be a pandas Series")
        if not values.index.equals(weights.index):
            raise ValueError("values and weights must have exactly the same index")
        if (weights.dropna() <= 0).any():
            raise ValueError("weights must be positive")

    encoded = pd.get_dummies(frame, drop_first=add_intercept, dtype=float)
    if encoded.shape[1] == 0 and not add_intercept:
        raise ValueError("exposures must produce at least one regression column")
    valid = values.notna() & frame.notna().all(axis=1) & encoded.notna().all(axis=1)
    if weights is not None:
        valid &= weights.notna()
    response = values.loc[valid].astype(float)
    design = encoded.loc[valid].to_numpy(dtype=float)
    if add_intercept:
        design = np.column_stack([np.ones(len(design)), design])
    if len(response) <= design.shape[1]:
        raise ValueError("neutralization requires more observations than regressors")
    response_values = response.to_numpy(dtype=float)
    if weights is not None:
        scale = np.sqrt(weights.loc[valid].to_numpy(dtype=float))
        coefficients = np.linalg.lstsq(
            design * scale[:, None], response_values * scale, rcond=None
        )[0]
    else:
        coefficients = np.linalg.lstsq(design, response_values, rcond=None)[0]
    result = pd.Series(np.nan, index=values.index, name=values.name, dtype=float)
    result.loc[valid] = response_values - design @ coefficients
    return result


def relative_strength(
    prices: pd.DataFrame,
    *,
    lookback: int = 21,
    method: RankMethod = "average",
) -> pd.DataFrame:
    """Rank trailing asset returns cross-sectionally for every timestamp.

    The input must be a time-by-asset price matrix. Output values are
    percentile ranks in ``(0, 1]``; larger values indicate stronger trailing
    performance relative to the contemporaneous universe.
    """
    numeric = _numeric_values(prices)
    if not isinstance(numeric, pd.DataFrame):
        raise TypeError("prices must be a pandas DataFrame")
    if isinstance(lookback, bool) or not isinstance(lookback, int) or lookback < 1:
        raise ValueError("lookback must be a positive integer")
    if (numeric.dropna() <= 0).any().any():
        raise ValueError("prices must be positive")
    trailing_returns = numeric.div(numeric.shift(lookback)).sub(1.0)
    return percentile_rank(trailing_returns, method=method)