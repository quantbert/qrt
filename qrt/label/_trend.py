"""Forward trend-scanning labels."""

from __future__ import annotations

from collections.abc import Iterable
from numbers import Integral
from typing import Any

import numpy as np
import pandas as pd

from qrt.label._validation import (
    event_index,
    non_negative_number,
    numeric_series,
)


def _trend_horizons(horizons: Iterable[int]) -> tuple[int, ...]:
    if isinstance(horizons, (str, bytes)):
        raise TypeError("horizons must be an iterable of integer bar counts")
    try:
        values = tuple(horizons)
    except TypeError as exc:
        raise TypeError("horizons must be an iterable of integer bar counts") from exc
    if not values:
        raise ValueError("horizons must not be empty")
    if any(
        not isinstance(value, Integral)
        or isinstance(value, bool)
        or int(value) < 2
        for value in values
    ):
        raise ValueError("every trend horizon must be an integer of at least 2 bars")
    result = tuple(int(value) for value in values)
    if any(left >= right for left, right in zip(result, result[1:])):
        raise ValueError("horizons must be unique and strictly increasing")
    return result


def _slope_t_value(values: np.ndarray) -> tuple[float, float]:
    x = np.arange(len(values), dtype=float)
    centered_x = x - x.mean()
    centered_y = values - values.mean()
    sum_squared_x = float(centered_x @ centered_x)
    slope = float(centered_x @ centered_y / sum_squared_x)
    residuals = values - (values.mean() + slope * centered_x)
    residual_variance = float(residuals @ residuals / (len(values) - 2))
    standard_error = float(np.sqrt(max(residual_variance, 0.0) / sum_squared_x))
    tolerance = np.finfo(float).eps * max(1.0, float(np.abs(values).max()))
    if standard_error <= tolerance:
        t_value = float(np.sign(slope) * np.inf) if slope != 0 else 0.0
    else:
        t_value = slope / standard_error
    return slope, t_value


def trend_scanning(
    prices: pd.Series,
    *,
    events: pd.Index | Iterable[Any] | None = None,
    horizons: Iterable[int] = range(5, 21),
    min_t_value: float = 0.0,
    log_prices: bool = True,
    drop_censored: bool = True,
) -> pd.DataFrame:
    """Label events using the strongest forward linear trend.

    For each event, ordinary least squares is fitted over every eligible
    forward horizon. The horizon whose slope has the largest absolute t-value
    is retained. A horizon of ``n`` means ``n`` bars after the event and fits
    ``n + 1`` observations including the event itself.

    Args:
        prices: Ordered prices for one instrument.
        events: Event labels drawn from ``prices.index``. Defaults to all.
        horizons: Unique, increasing forward bar counts of at least 2.
        min_t_value: Absolute t-value required for a directional label.
        log_prices: Regress log prices, making slope units approximately
            continuously compounded return per bar.
        drop_censored: Drop events for which no requested horizon is complete.

    Returns:
        DataFrame containing the selected end time, horizon, slope, t-value,
        realized return, and directional label.
    """
    if not isinstance(log_prices, bool):
        raise TypeError("log_prices must be a boolean")
    if not isinstance(drop_censored, bool):
        raise TypeError("drop_censored must be a boolean")
    close = numeric_series(prices, "prices", positive=True)
    event_times = event_index(events, close.index)
    candidate_horizons = _trend_horizons(horizons)
    boundary = non_negative_number(min_t_value, "min_t_value")
    regression_values = np.log(close.to_numpy()) if log_prices else close.to_numpy()

    selected_event_positions: list[int] = []
    end_times: list[Any] = []
    selected_horizons: list[Any] = []
    slopes: list[float] = []
    t_values: list[float] = []
    returns: list[float] = []
    labels: list[Any] = []
    missing_time = pd.NaT if isinstance(close.index, pd.DatetimeIndex) else None

    for event_offset, (event, start) in enumerate(
        zip(event_times, close.index.get_indexer(event_times), strict=True)
    ):
        best: tuple[int, float, float] | None = None
        for horizon in candidate_horizons:
            end = start + horizon
            if end >= len(close):
                break
            slope, t_value = _slope_t_value(regression_values[start : end + 1])
            if best is None or abs(t_value) > abs(best[2]):
                best = (horizon, slope, t_value)

        if best is None:
            if drop_censored:
                continue
            selected_event_positions.append(event_offset)
            end_times.append(missing_time)
            selected_horizons.append(pd.NA)
            slopes.append(np.nan)
            t_values.append(np.nan)
            returns.append(np.nan)
            labels.append(pd.NA)
            continue

        horizon, slope, t_value = best
        end = start + horizon
        realized = float(close.iloc[end] / close.iloc[start] - 1.0)
        selected_event_positions.append(event_offset)
        end_times.append(close.index[end])
        selected_horizons.append(horizon)
        slopes.append(slope)
        t_values.append(t_value)
        returns.append(realized)
        labels.append(int(np.sign(t_value)) if abs(t_value) > boundary else 0)

    return pd.DataFrame(
        {
            "end_time": end_times,
            "horizon": pd.array(selected_horizons, dtype="Int64"),
            "slope": slopes,
            "t_value": t_values,
            "return": returns,
            "label": pd.array(labels, dtype="Int8"),
        },
        index=event_times.take(selected_event_positions).rename("event_time"),
    )