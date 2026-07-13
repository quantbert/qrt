"""Lagged copies of a Series or DataFrame."""

from collections.abc import Iterable

import pandas as pd


def lags(
    data: pd.Series | pd.DataFrame,
    lags: int | Iterable[int],
) -> pd.DataFrame:
    """Create lagged copies of a Series or DataFrame.

    Args:
        data: Input series or frame (rows ordered in time).
        lags: Number of lags (1..n) or an explicit iterable of lag periods.

    Returns:
        DataFrame with one column per (column, lag), named ``{name}_lag{k}``.

    Examples:
        >>> q.feat.qta.lags(prices["close"], 3)      # close_lag1..close_lag3
        >>> q.feat.qta.lags(df, [1, 5, 21])          # daily, weekly, monthly lags
    """
    periods = range(1, lags + 1) if isinstance(lags, int) else list(lags)
    frame = data.to_frame() if isinstance(data, pd.Series) else data
    out = {
        f"{col}_lag{k}": frame[col].shift(k)
        for col in frame.columns
        for k in periods
    }
    return pd.DataFrame(out, index=frame.index)
