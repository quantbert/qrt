"""Exponential moving average."""

import pandas as pd


def ema(series: pd.Series, window: int) -> pd.Series:
    """Calculate an exponential moving average.

    Args:
        series: Input series.
        window: Exponential span, in periods.

    Returns:
        Exponential moving average with the input index preserved.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("series must be a pandas Series")
    if not isinstance(window, int) or isinstance(window, bool) or window <= 0:
        raise ValueError("window must be a positive integer")
    return series.ewm(span=window, adjust=False).mean()