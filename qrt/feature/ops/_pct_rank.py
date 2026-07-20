"""Rolling percentile rank."""

import pandas as pd


def pct_rank(series: pd.Series, window: int = 60) -> pd.Series:
    """Calculate each value's percentile rank in a trailing window."""
    return series.rolling(window).rank(pct=True) * 100.0