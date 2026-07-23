"""Fixed-horizon and triple-barrier target construction."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import timedelta
from numbers import Integral
from typing import Any

import numpy as np
import pandas as pd

from qrt.label._validation import (
    aligned_numeric_values,
    event_index,
    non_negative_number,
    numeric_series,
    positive_number,
    validate_index,
)

Horizon = int | str | timedelta | np.timedelta64 | pd.Timedelta


def _horizon_positions(
    observations: pd.Index,
    events: pd.Index,
    horizon: Horizon,
) -> np.ndarray:
    starts = observations.get_indexer(events)
    if isinstance(horizon, Integral) and not isinstance(horizon, bool):
        steps = int(horizon)
        if steps <= 0:
            raise ValueError("horizon must be a positive number of bars")
        ends = starts + steps
    else:
        if not isinstance(observations, pd.DatetimeIndex):
            raise TypeError("a timedelta horizon requires a DatetimeIndex")
        try:
            duration = pd.Timedelta(horizon)
        except (TypeError, ValueError) as exc:
            raise ValueError("horizon must be a positive timedelta") from exc
        if duration <= pd.Timedelta(0):
            raise ValueError("horizon must be a positive timedelta")
        ends = observations.searchsorted(events + duration, side="left")

    return np.where(ends < len(observations), ends, -1).astype(int)


def _labels_at_positions(index: pd.Index, positions: np.ndarray) -> list[Any]:
    missing = pd.NaT if isinstance(index, pd.DatetimeIndex) else None
    return [missing if position < 0 else index[position] for position in positions]


def vertical_barriers(
    observations: pd.Index,
    horizon: Horizon,
    *,
    events: pd.Index | Iterable[Any] | None = None,
) -> pd.Series:
    """Map events to the first observation at or beyond a future horizon.

    Integer horizons count observations after each event. Timedelta-like
    horizons use the first observed timestamp greater than or equal to the
    requested wall-clock duration. Events without enough future data receive a
    missing barrier.

    Args:
        observations: Ordered, unique observation index.
        horizon: Positive number of bars or a positive timedelta-like value.
        events: Event labels drawn from ``observations``. Defaults to every
            observation.

    Returns:
        Series indexed by event start time, named ``event_time``, and
        containing vertical-barrier times. The index is the pandas alignment
        key for other event-indexed objects.
    """
    validate_index(observations, "observations")
    event_times = event_index(events, observations)
    positions = _horizon_positions(observations, event_times, horizon)
    return pd.Series(
        _labels_at_positions(observations, positions),
        index=event_times.rename("event_time"),
        name="vertical_barrier",
    )


def _explicit_vertical_positions(
    vertical: pd.Series,
    observations: pd.Index,
    events: pd.Index,
) -> np.ndarray:
    if not isinstance(vertical, pd.Series):
        raise TypeError("vertical must be a pandas Series")
    validate_index(vertical.index, "vertical index")
    if not events.isin(vertical.index).all():
        raise ValueError("vertical must contain every event")

    starts = observations.get_indexer(events)
    ends = np.full(len(events), -1, dtype=int)
    for offset, endpoint in enumerate(vertical.reindex(events)):
        if pd.isna(endpoint):
            continue
        position = observations.get_indexer([endpoint])[0]
        if position < 0:
            raise ValueError("every vertical barrier must be in the prices index")
        if position <= starts[offset]:
            raise ValueError("every vertical barrier must occur after its event")
        ends[offset] = position
    return ends


def _end_positions(
    observations: pd.Index,
    events: pd.Index,
    horizon: Horizon | None,
    vertical: pd.Series | None,
) -> np.ndarray:
    if (horizon is None) == (vertical is None):
        raise ValueError("provide exactly one of horizon or vertical")
    if vertical is not None:
        return _explicit_vertical_positions(vertical, observations, events)
    return _horizon_positions(observations, events, horizon)


def _validate_drop_censored(drop_censored: bool) -> None:
    if not isinstance(drop_censored, bool):
        raise TypeError("drop_censored must be a boolean")


def fixed_horizon(
    prices: pd.Series,
    horizon: Horizon,
    *,
    events: pd.Index | Iterable[Any] | None = None,
    threshold: float | pd.Series = 0.0,
    drop_censored: bool = True,
) -> pd.DataFrame:
    """Label future returns at a fixed horizon.

    Returns above ``threshold`` receive label 1, returns below its negative
    receive -1, and values inside the neutral band receive 0. Missing dynamic
    thresholds are excluded. By default, events without a complete future
    horizon are also excluded.

    Args:
        prices: Ordered positive prices for one instrument.
        horizon: Positive number of bars or positive timedelta-like value.
        events: Event labels drawn from ``prices.index``. Defaults to all.
        threshold: Non-negative scalar or event-aligned neutral-band width.
        drop_censored: Drop events whose horizon extends past available data.

    Returns:
        DataFrame indexed by event start time, named ``event_time``, with end
        time, realized return, threshold, and label. The index aligns rows with
        event-time features and metadata in pandas operations.
    """
    close = numeric_series(prices, "prices", positive=True)
    _validate_drop_censored(drop_censored)
    event_times = event_index(events, close.index)
    thresholds = aligned_numeric_values(
        threshold,
        event_times,
        "threshold",
        allow_missing=True,
        non_negative=True,
    )
    eligible = thresholds.notna().to_numpy()
    event_times = event_times[eligible]
    thresholds = thresholds.iloc[np.flatnonzero(eligible)]
    end_positions = _horizon_positions(close.index, event_times, horizon)

    if drop_censored:
        complete = end_positions >= 0
        event_times = event_times[complete]
        thresholds = thresholds.iloc[np.flatnonzero(complete)]
        end_positions = end_positions[complete]

    start_positions = close.index.get_indexer(event_times)
    end_times = _labels_at_positions(close.index, end_positions)
    returns = np.full(len(event_times), np.nan, dtype=float)
    labels: list[Any] = []
    for start, end, boundary in zip(
        start_positions,
        end_positions,
        thresholds.to_numpy(),
        strict=True,
    ):
        if end < 0:
            labels.append(pd.NA)
            continue
        realized = float(close.iloc[end] / close.iloc[start] - 1.0)
        returns[len(labels)] = realized
        labels.append(1 if realized > boundary else -1 if realized < -boundary else 0)

    result = pd.DataFrame(
        {
            "end_time": end_times,
            "return": returns,
            "threshold": thresholds.to_numpy(),
            "label": pd.array(labels, dtype="Int8"),
        },
        index=event_times.rename("event_time"),
    )
    return result


def triple_barrier(
    prices: pd.Series,
    target: float | pd.Series,
    *,
    events: pd.Index | Iterable[Any] | None = None,
    horizon: Horizon | None = None,
    vertical: pd.Series | None = None,
    upper: float | None = 1.0,
    lower: float | None = 1.0,
    side: float | pd.Series | None = None,
    min_target: float = 0.0,
    drop_censored: bool = True,
) -> pd.DataFrame:
    """Apply profit-taking, stop-loss, and vertical barriers to events.

    Horizontal barriers are multiples of an event-specific return target. The
    first barrier touched by the close-price path determines ``touch_time``.
    Without ``side``, labels are directional (-1, 0, 1). With an explicit
    side, returns are side-adjusted for barrier detection and labels become
    binary meta-labels: 1 for a profitable side and 0 otherwise.

    Args:
        prices: Ordered positive close prices for one instrument.
        target: Positive scalar or Series of event-specific return widths.
            Missing Series values and values at or below ``min_target`` are
            excluded.
        events: Event labels drawn from ``prices.index``. Defaults to all.
        horizon: Positive bar count or timedelta-like vertical horizon.
        vertical: Explicit event-indexed vertical-barrier times. Supply exactly
            one of ``horizon`` or ``vertical``.
        upper: Profit-taking multiplier. ``None`` disables this barrier.
        lower: Stop-loss multiplier. ``None`` disables this barrier.
        side: Optional scalar or event-aligned Series containing -1 or 1.
        min_target: Minimum eligible target width.
        drop_censored: Drop events without a complete vertical horizon.

    Returns:
        DataFrame indexed by event start time, named ``event_time``, describing
        barriers, realized returns, and labels. The index aligns rows with
        event-time features and metadata in pandas operations. Side-aware
        results also include ``side`` and ``adjusted_return``.
    """
    close = numeric_series(prices, "prices", positive=True)
    _validate_drop_censored(drop_censored)
    minimum = non_negative_number(min_target, "min_target")
    upper_multiplier = None if upper is None else positive_number(upper, "upper")
    lower_multiplier = None if lower is None else positive_number(lower, "lower")

    event_times = event_index(events, close.index)
    targets = aligned_numeric_values(
        target,
        event_times,
        "target",
        allow_missing=True,
        non_negative=True,
    )
    eligible = targets.notna() & targets.gt(minimum)
    event_times = event_times[eligible.to_numpy()]
    targets = targets.iloc[np.flatnonzero(eligible.to_numpy())]

    sides: pd.Series | None = None
    if side is not None:
        sides = aligned_numeric_values(side, event_times, "side")
        if not np.isin(sides.to_numpy(), [-1.0, 1.0]).all():
            raise ValueError("side must contain only -1 or 1")

    end_positions = _end_positions(close.index, event_times, horizon, vertical)
    if drop_censored:
        complete = end_positions >= 0
        event_times = event_times[complete]
        targets = targets.iloc[np.flatnonzero(complete)]
        if sides is not None:
            sides = sides.iloc[np.flatnonzero(complete)]
        end_positions = end_positions[complete]

    start_positions = close.index.get_indexer(event_times)
    vertical_times = _labels_at_positions(close.index, end_positions)
    touch_times: list[Any] = []
    barrier_names: list[str] = []
    raw_returns: list[float] = []
    adjusted_returns: list[float] = []
    labels: list[Any] = []

    side_values = (
        sides.to_numpy() if sides is not None else np.ones(len(event_times), dtype=float)
    )
    for start, end, width, event_side in zip(
        start_positions,
        end_positions,
        targets.to_numpy(),
        side_values,
        strict=True,
    ):
        scan_end = end if end >= 0 else len(close) - 1
        path_positions = np.arange(start + 1, scan_end + 1)
        path_returns = (
            close.iloc[path_positions].to_numpy() / float(close.iloc[start]) - 1.0
        )
        adjusted_path = path_returns * event_side

        upper_touch = np.flatnonzero(adjusted_path >= upper_multiplier * width)[0] if (
            upper_multiplier is not None
            and np.any(adjusted_path >= upper_multiplier * width)
        ) else None
        lower_touch = np.flatnonzero(adjusted_path <= -lower_multiplier * width)[0] if (
            lower_multiplier is not None
            and np.any(adjusted_path <= -lower_multiplier * width)
        ) else None

        if upper_touch is not None and (
            lower_touch is None or upper_touch < lower_touch
        ):
            touch_position = int(path_positions[upper_touch])
            barrier = "upper"
        elif lower_touch is not None:
            touch_position = int(path_positions[lower_touch])
            barrier = "lower"
        elif end >= 0:
            touch_position = int(end)
            barrier = "vertical"
        else:
            touch_times.append(pd.NaT if isinstance(close.index, pd.DatetimeIndex) else None)
            barrier_names.append("censored")
            raw_returns.append(np.nan)
            adjusted_returns.append(np.nan)
            labels.append(pd.NA)
            continue

        realized = float(close.iloc[touch_position] / close.iloc[start] - 1.0)
        adjusted = realized * event_side
        touch_times.append(close.index[touch_position])
        barrier_names.append(barrier)
        raw_returns.append(realized)
        adjusted_returns.append(adjusted)
        labels.append(
            int(adjusted > 0) if sides is not None else int(np.sign(adjusted))
        )

    data: dict[str, Any] = {
        "vertical_barrier": vertical_times,
        "touch_time": touch_times,
        "barrier": pd.array(barrier_names, dtype="string"),
        "target": targets.to_numpy(),
    }
    if sides is not None:
        data["side"] = sides.to_numpy()
    data["return"] = raw_returns
    if sides is not None:
        data["adjusted_return"] = adjusted_returns
    data["label"] = pd.array(labels, dtype="Int8")
    return pd.DataFrame(data, index=event_times.rename("event_time"))