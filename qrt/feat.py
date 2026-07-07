"""Feature engineering: indicators and wrappers around feature libraries."""

import pandas as pd


def SMA(series: pd.Series, window: int) -> pd.Series:
    """Simple moving average."""
    return series.rolling(window).mean()
