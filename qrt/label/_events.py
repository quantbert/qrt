"""Event detection for financial labeling workflows."""

from __future__ import annotations

import numpy as np
import pandas as pd

from qrt.label._validation import non_negative_number, numeric_series


def cusum_filter(
    prices: pd.Series,
    threshold: float | pd.Series,
    *,
    drift: float = 0.0,
    log_returns: bool = True,
) -> pd.Index:
    """Detect structural events with a symmetric CUSUM filter.

    Positive and negative cumulative changes are tracked independently. An
    event is emitted when either accumulator crosses ``threshold``; the
    triggered accumulator is then reset. With ``log_returns=True``, thresholds
    and drift are expressed as decimal log returns.

    Args:
        prices: Ordered prices for one instrument.
        threshold: Positive scalar or an aligned Series of time-varying
            thresholds. Missing Series values suppress events and reset the
            accumulators at those observations.
        drift: Non-negative drift subtracted from each directional increment.
        log_returns: Use log-price changes instead of arithmetic differences.

    Returns:
        Index containing the timestamps where a threshold was crossed.
    """
    close = numeric_series(prices, "prices", positive=log_returns)
    drift_value = non_negative_number(drift, "drift")

    if isinstance(threshold, pd.Series):
        thresholds = numeric_series(
            threshold,
            "threshold",
            allow_missing=True,
            positive=True,
        )
        if not thresholds.index.equals(close.index):
            raise ValueError("threshold index must match prices index")
    else:
        threshold_value = non_negative_number(threshold, "threshold")
        if threshold_value == 0:
            raise ValueError("threshold must be positive")
        thresholds = pd.Series(threshold_value, index=close.index)

    changes = np.log(close).diff() if log_returns else close.diff()
    positive_sum = 0.0
    negative_sum = 0.0
    event_positions: list[int] = []

    for position in range(1, len(close)):
        change = changes.iloc[position]
        boundary = thresholds.iloc[position]
        if pd.isna(change) or pd.isna(boundary):
            positive_sum = 0.0
            negative_sum = 0.0
            continue

        positive_sum = max(0.0, positive_sum + float(change) - drift_value)
        negative_sum = min(0.0, negative_sum + float(change) + drift_value)
        if negative_sum < -float(boundary):
            negative_sum = 0.0
            event_positions.append(position)
        elif positive_sum > float(boundary):
            positive_sum = 0.0
            event_positions.append(position)

    return close.index.take(event_positions)