"""Causal timing, persistence, and exposure controls for signals."""

from __future__ import annotations

import numpy as np
import pandas as pd

from qrt.signal._validation import (
    SignalLike,
    as_signal,
    directional,
    finite_number,
    non_negative_integer,
    positive_number,
)


def delay(values: SignalLike, periods: int = 1) -> SignalLike:
    """Delay intent by an explicit number of observations.

    The default one-row delay makes a score observed at row ``t`` available as
    intent at row ``t + 1``. A zero delay is allowed only when same-row
    availability is deliberate.
    """
    signal = as_signal(values)
    lag = non_negative_integer(periods, "periods")
    return signal.shift(lag)


def decay(values: SignalLike, *, half_life: float) -> SignalLike:
    """Exponentially smooth signal updates using only current and prior rows."""
    signal = as_signal(values)
    half_life_value = positive_number(half_life, "half_life")
    return signal.ewm(
        halflife=half_life_value,
        adjust=False,
        min_periods=1,
    ).mean()


def hold(values: SignalLike, *, periods: int) -> SignalLike:
    """Enforce a minimum observation count between directional state changes.

    Missing proposals remain missing and do not change the held state. A
    ``periods`` value of one permits a change on every adjacent observation.
    """
    signal = directional(values)
    minimum = non_negative_integer(periods, "periods")
    if minimum < 1:
        raise ValueError("periods must be at least 1")

    def apply(series: pd.Series) -> pd.Series:
        output = pd.Series(np.nan, index=series.index, name=series.name)
        state: float | None = None
        changed_at: int | None = None
        for position, proposed in enumerate(series.to_numpy(dtype=float)):
            if np.isnan(proposed):
                continue
            if state is None:
                state = proposed
                changed_at = position
            elif proposed != state and position - int(changed_at) >= minimum:
                state = proposed
                changed_at = position
            output.iloc[position] = state
        return output

    if isinstance(signal, pd.Series):
        return apply(signal)
    return signal.apply(apply, axis="index")


def cooldown(values: SignalLike, *, periods: int) -> SignalLike:
    """Require flat observations before re-entering a directional signal.

    Exits are immediate. A direct sign reversal is treated as an exit, and the
    opposite side may enter only after ``periods`` subsequent rows have been
    kept flat.
    """
    signal = directional(values)
    wait = non_negative_integer(periods, "periods")

    def apply(series: pd.Series) -> pd.Series:
        output = pd.Series(np.nan, index=series.index, name=series.name)
        state = 0.0
        blocked_through = -1
        for position, proposed in enumerate(series.to_numpy(dtype=float)):
            if np.isnan(proposed):
                continue
            if state != 0.0 and proposed != state:
                state = 0.0
                blocked_through = position + wait
            elif state == 0.0 and proposed != 0.0 and position > blocked_through:
                state = proposed
            output.iloc[position] = state
        return output

    if isinstance(signal, pd.Series):
        return apply(signal)
    return signal.apply(apply, axis="index")


def limit_turnover(
    values: SignalLike,
    *,
    max_change: float,
    initial: float = 0.0,
) -> SignalLike:
    """Limit each row's per-asset target change from the prior accepted value."""
    signal = as_signal(values)
    change = positive_number(max_change, "max_change")
    initial_value = finite_number(initial, "initial")

    def apply(series: pd.Series) -> pd.Series:
        previous = initial_value
        output = pd.Series(np.nan, index=series.index, name=series.name)
        for position, proposed in enumerate(series.to_numpy(dtype=float)):
            if np.isnan(proposed):
                continue
            previous = float(np.clip(proposed, previous - change, previous + change))
            output.iloc[position] = previous
        return output

    if isinstance(signal, pd.Series):
        return apply(signal)
    return signal.apply(apply, axis="index")


def target_exposure(
    values: SignalLike,
    *,
    maximum: float = 1.0,
    clip: bool = True,
) -> SignalLike:
    """Map normalized conviction to per-asset desired exposure.

    Values in ``[-1, 1]`` map linearly to ``[-maximum, maximum]``. By default,
    stronger scores are clipped to that conviction range. This function does
    not impose portfolio gross, net, leverage, or capital constraints.
    """
    signal = as_signal(values)
    maximum_value = positive_number(maximum, "maximum")
    if not isinstance(clip, bool):
        raise TypeError("clip must be a bool")
    observed = signal.to_numpy(dtype=float)
    if not clip and (np.abs(observed[~np.isnan(observed)]) > 1.0).any():
        raise ValueError("values must lie within [-1, 1] when clip is False")
    conviction = signal.clip(lower=-1.0, upper=1.0) if clip else signal
    return conviction * maximum_value