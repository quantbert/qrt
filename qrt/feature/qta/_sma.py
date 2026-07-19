"""Simple moving average."""

import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    """Simple moving average.

    Args:
        series: Input series (e.g. close prices).
        window: Rolling window size, in periods.

    Returns:
        Series of the rolling mean, with the same index as ``series``.

    Examples:
        >>> q.feature.qta.sma(prices["close"], 20)      # 20-period SMA
    """
    return series.rolling(window).mean()
