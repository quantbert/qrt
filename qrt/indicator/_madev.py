"""Mean absolute deviation from a moving average."""

import numpy as np
import pandas as pd


def madev(prices: pd.Series, window: int = 20) -> pd.Series:
    """Calculate rolling mean absolute deviation from a rolling SMA.

    The absolute deviation from the ``window``-period simple moving average is
    itself averaged over ``window`` periods. The first defined result therefore
    requires ``2 * window - 1`` observations.

    Args:
        prices: Prices for one instrument.
        window: Window used for both rolling calculations.

    Returns:
        MADEV Series preserving the input index.
    """
    if not isinstance(prices, pd.Series):
        raise TypeError("prices must be a pandas Series")
    if not isinstance(window, int) or isinstance(window, bool) or window <= 0:
        raise ValueError("window must be a positive integer")
    if not pd.api.types.is_numeric_dtype(prices):
        raise TypeError("prices must contain numeric values")
    if prices.index.has_duplicates:
        raise ValueError("prices index must not contain duplicates")

    values = prices.astype(float)
    if np.isinf(values.dropna().to_numpy()).any():
        raise ValueError("prices must not contain infinite values")

    average = values.rolling(window=window, min_periods=window).mean()
    result = (values - average).abs().rolling(window=window, min_periods=window).mean()
    return result.rename("madev")
