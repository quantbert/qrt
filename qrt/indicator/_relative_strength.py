"""Relative-strength time-series features."""

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


def _positive_window(window: int) -> None:
    if not isinstance(window, int) or isinstance(window, bool) or window <= 0:
        raise ValueError("window must be a positive integer")


def _align_reference(reference: pd.Series, index: pd.Index, name: str) -> pd.Series:
    values = _numeric_series(reference, name).reindex(index)
    if values.notna().sum() == 0:
        raise ValueError(f"{name} must overlap the asset index")
    return values


def relative_strength(
    prices: pd.Series,
    benchmark: pd.Series,
    lookback: int = 21,
) -> pd.Series:
    """Calculate asset return minus benchmark return over a lookback.

    The benchmark is aligned to the asset index without filling missing dates.

    Args:
        prices: Prices for one asset.
        benchmark: Benchmark prices.
        lookback: Return lookback, in periods.

    Returns:
        Relative-strength Series preserving the asset index.
    """
    _positive_window(lookback)
    asset = _numeric_series(prices, "prices")
    reference = _align_reference(benchmark, asset.index, "benchmark")
    asset_return = asset.pct_change(periods=lookback, fill_method=None)
    benchmark_return = reference.pct_change(periods=lookback, fill_method=None)
    return (asset_return - benchmark_return).rename("relative_strength")


def rs_days(
    relative_strength: pd.Series,
    benchmark: pd.Series,
    window: int = 60,
    correction_threshold: float = 0.95,
) -> pd.Series:
    """Count recent positive relative-strength periods during a correction.

    A correction is a benchmark price below ``correction_threshold`` times its
    rolling high.
    """
    _positive_window(window)
    if not 0 < correction_threshold < 1:
        raise ValueError("correction_threshold must be between 0 and 1")
    strength = _numeric_series(relative_strength, "relative_strength")
    reference = _align_reference(benchmark, strength.index, "benchmark")
    rolling_high = reference.rolling(window=window).max()
    correction = reference < rolling_high * correction_threshold
    positive_during_correction = ((strength > 0) & correction).astype(int)
    return positive_during_correction.rolling(window=window).sum().rename("rs_days")


def rsma(
    relative_strength: pd.Series,
    window: int = 21,
    method: Literal["exponential", "simple"] = "exponential",
) -> pd.Series:
    """Smooth a relative-strength Series."""
    _positive_window(window)
    strength = _numeric_series(relative_strength, "relative_strength")
    if method == "exponential":
        result = strength.ewm(span=window, adjust=False).mean()
    elif method == "simple":
        result = strength.rolling(window=window).mean()
    else:
        raise ValueError("method must be 'exponential' or 'simple'")
    return result.rename("rsma")


def rs_phase(
    relative_strength: pd.Series,
    moving_average: pd.Series,
) -> pd.DataFrame:
    """Flag and count consecutive periods above a relative-strength average."""
    strength = _numeric_series(relative_strength, "relative_strength")
    average = _align_reference(moving_average, strength.index, "moving_average")
    above = strength.notna() & average.notna() & strength.gt(average)
    days = above.groupby((~above).cumsum()).cumsum().astype(int)
    return pd.DataFrame({"rs_phase": above, "rs_phase_days": days}, index=strength.index)


def rsnhbp(
    prices: pd.Series,
    relative_strength: pd.Series,
    window: int = 60,
) -> pd.Series:
    """Flag a relative-strength high that precedes a price high."""
    _positive_window(window)
    asset = _numeric_series(prices, "prices")
    strength = _align_reference(relative_strength, asset.index, "relative_strength")
    previous_strength_high = strength.shift(1).rolling(window, min_periods=1).max()
    previous_price_high = asset.shift(1).rolling(window, min_periods=1).max()
    signal = strength.gt(previous_strength_high) & ~asset.gt(previous_price_high)
    return signal.rename("rs_new_high_before_price")