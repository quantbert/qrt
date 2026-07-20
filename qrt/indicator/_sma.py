"""Simple moving average."""

import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    """Calculate a simple moving average.

    Args:
        series: Input series.
        window: Rolling window size, in periods.

    Returns:
        Rolling mean with the input index preserved.

    Examples:
        >>> q.indicator.sma(prices["close"], 20)
    """
    return series.rolling(window).mean()