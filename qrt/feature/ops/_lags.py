"""Lagged copies of a Series or DataFrame."""

from collections.abc import Iterable

import pandas as pd


def lags(
    data: pd.Series | pd.DataFrame,
    lags: int | Iterable[int],
) -> pd.DataFrame:
    """Create lagged copies of a Series or DataFrame."""
    periods = range(1, lags + 1) if isinstance(lags, int) else list(lags)
    frame = data.to_frame() if isinstance(data, pd.Series) else data
    out = {
        f"{column}_lag{period}": frame[column].shift(period)
        for column in frame.columns
        for period in periods
    }
    return pd.DataFrame(out, index=frame.index)