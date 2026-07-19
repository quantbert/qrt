"""Rolling percentile rank."""

import pandas as pd


def pct_rank(series: pd.Series, window: int = 60) -> pd.Series:
    """Rolling percentile rank of each value within a trailing window.

    Useful for gauging whether a price or indicator value is relatively high or low
    compared to its own recent history, independent of absolute scale.

    Args:
        series: Input series (e.g. close prices or an indicator).
        window: Rolling window size, in periods.

    Returns:
        Series of percentile ranks (0-100 scale), same index as ``series``. The
        first ``window - 1`` values are ``NaN`` (insufficient history).

    Examples:
        >>> q.feat.qta.pct_rank(prices["close"], 60)   # rank vs trailing 60 periods
    """
    return series.rolling(window).rank(pct=True) * 100.0
