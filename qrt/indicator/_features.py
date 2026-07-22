"""Common return, momentum, volatility, and volume measurements."""

from typing import Literal

import numpy as np
import pandas as pd


def _numeric_series(series: pd.Series, name: str) -> pd.Series:
    if not isinstance(series, pd.Series):
        raise TypeError(f"{name} must be a pandas Series")
    if not pd.api.types.is_numeric_dtype(series):
        raise TypeError(f"{name} must contain numeric values")
    if series.index.has_duplicates:
        raise ValueError(f"{name} index must not contain duplicates")
    values = series.astype(float)
    if np.isinf(values.dropna().to_numpy()).any():
        raise ValueError(f"{name} must not contain infinite values")
    return values


def _positive_integer(value: int, name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def returns(prices: pd.Series, periods: int = 1) -> pd.Series:
    """Calculate simple price returns over a number of periods.

    Args:
        prices: Prices for one instrument.
        periods: Number of observations between prices.

    Returns:
        Percentage-change Series preserving the input index.
    """
    _positive_integer(periods, "periods")
    values = _numeric_series(prices, "prices")
    return values.pct_change(periods=periods, fill_method=None).rename("returns")


def momentum(prices: pd.Series, window: int = 20) -> pd.Series:
    """Calculate simple price momentum over a rolling lookback.

    Args:
        prices: Prices for one instrument.
        window: Return lookback, in periods.

    Returns:
        Percentage-change Series preserving the input index.
    """
    _positive_integer(window, "window")
    values = _numeric_series(prices, "prices")
    return values.pct_change(periods=window, fill_method=None).rename("momentum")


def rolling_volatility(
    returns: pd.Series,
    window: int = 20,
    *,
    min_periods: int | None = None,
    ddof: int = 1,
) -> pd.Series:
    """Calculate rolling standard deviation of a return Series.

    Args:
        returns: Returns for one instrument.
        window: Rolling window size, in periods.
        min_periods: Minimum observations required. Defaults to ``window``.
        ddof: Delta degrees of freedom used by the standard deviation.

    Returns:
        Rolling volatility Series preserving the input index.
    """
    _positive_integer(window, "window")
    if min_periods is not None:
        _positive_integer(min_periods, "min_periods")
        if min_periods > window:
            raise ValueError("min_periods must not exceed window")
    if not isinstance(ddof, int) or isinstance(ddof, bool) or ddof < 0:
        raise ValueError("ddof must be a non-negative integer")
    values = _numeric_series(returns, "returns")
    return (
        values.rolling(window=window, min_periods=min_periods).std(ddof=ddof)
        .rename("rolling_volatility")
    )


def volume_ratio(
    volume: pd.Series,
    window: int = 20,
    *,
    statistic: Literal["mean", "median"] = "median",
    min_periods: int | None = None,
) -> pd.Series:
    """Calculate volume relative to a rolling baseline.

    Args:
        volume: Non-negative volume observations for one instrument.
        window: Rolling baseline window, in periods.
        statistic: Baseline statistic, either ``"mean"`` or ``"median"``.
        min_periods: Minimum observations required. Defaults to ``window``.

    Returns:
        Relative-volume Series preserving the input index.
    """
    _positive_integer(window, "window")
    if min_periods is not None:
        _positive_integer(min_periods, "min_periods")
        if min_periods > window:
            raise ValueError("min_periods must not exceed window")
    values = _numeric_series(volume, "volume")
    if (values.dropna() < 0).any():
        raise ValueError("volume must not contain negative values")
    rolling = values.rolling(window=window, min_periods=min_periods)
    if statistic == "mean":
        baseline = rolling.mean()
    elif statistic == "median":
        baseline = rolling.median()
    else:
        raise ValueError("statistic must be 'mean' or 'median'")
    return values.div(baseline.replace(0, np.nan)).rename("volume_ratio")