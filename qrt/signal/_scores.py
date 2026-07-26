"""Convert model scores and rules into investment intent."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

import numpy as np
import pandas as pd

from qrt.cross_section import neutralize as _neutralize_snapshot
from qrt.cross_section import rank as _rank
from qrt.cross_section import zscore as _zscore
from qrt.signal._validation import (
    SignalLike,
    as_signal,
    finite_number,
    non_negative_integer,
)


def threshold(
    values: SignalLike,
    *,
    long_above: float,
    short_below: float | None = None,
) -> SignalLike:
    """Map scores to long, flat, and optionally short directional intent."""
    signal = as_signal(values)
    long_level = finite_number(long_above, "long_above")
    short_level = (
        None if short_below is None else finite_number(short_below, "short_below")
    )
    if short_level is not None:
        if short_level >= long_level:
            raise ValueError("short_below must be less than long_above")

    result = signal * 0.0
    result = result.mask(signal >= long_level, 1.0)
    if short_level is not None:
        result = result.mask(signal <= short_level, -1.0)
    return result


def hysteresis(
    values: SignalLike,
    *,
    long_enter: float,
    long_exit: float,
    short_enter: float | None = None,
    short_exit: float | None = None,
    initial: Literal[-1, 0, 1] = 0,
) -> SignalLike:
    """Create stable directional intent with separate entry and exit levels.

    Missing scores produce missing output and leave the internal state
    unchanged. When short levels are supplied, a score may reverse directly
    from long to short or short to long at the corresponding entry level.
    """
    signal = as_signal(values)
    long_enter_level = finite_number(long_enter, "long_enter")
    long_exit_level = finite_number(long_exit, "long_exit")
    if long_exit_level >= long_enter_level:
        raise ValueError("long_exit must be less than long_enter")
    has_short = short_enter is not None or short_exit is not None
    if has_short and (short_enter is None or short_exit is None):
        raise ValueError("short_enter and short_exit must be provided together")
    if has_short:
        short_enter_level = finite_number(short_enter, "short_enter")
        short_exit_level = finite_number(short_exit, "short_exit")
        if not short_enter_level < short_exit_level <= long_exit_level:
            raise ValueError(
                "levels must satisfy short_enter < short_exit <= long_exit < long_enter"
            )
    else:
        short_enter_level = None
        short_exit_level = None
    if initial not in (-1, 0, 1) or (initial == -1 and not has_short):
        raise ValueError("initial must be an enabled directional state")

    def apply(series: pd.Series) -> pd.Series:
        state = int(initial)
        output = pd.Series(np.nan, index=series.index, name=series.name)
        for position, score in enumerate(series.to_numpy(dtype=float)):
            if np.isnan(score):
                continue
            if state == 0:
                if score >= long_enter_level:
                    state = 1
                elif has_short and score <= short_enter_level:
                    state = -1
            elif state == 1:
                if has_short and score <= short_enter_level:
                    state = -1
                elif score <= long_exit_level:
                    state = 0
            elif score >= long_enter_level:
                state = 1
            elif score >= short_exit_level:
                state = 0
            output.iloc[position] = float(state)
        return output

    if isinstance(signal, pd.Series):
        return apply(signal)
    return signal.apply(apply, axis="index")


def normalize(
    values: pd.DataFrame,
    *,
    method: Literal["zscore", "percentile"] = "zscore",
) -> pd.DataFrame:
    """Normalize each timestamp's scores across the available asset universe.

    ``"percentile"`` maps ranks to ``[-1, 1]`` with zero for a one-asset
    cross-section. ``"zscore"`` delegates to `q.cross_section.zscore`.
    """
    signal = as_signal(values)
    if not isinstance(signal, pd.DataFrame):
        raise TypeError("values must be a time-by-asset pandas DataFrame")
    if method == "zscore":
        return _zscore(signal)
    if method != "percentile":
        raise ValueError("method must be one of 'zscore', 'percentile'")
    ranks = _rank(signal, method="average")
    counts = signal.notna().sum(axis="columns")
    scale = counts.sub(1).replace(0, np.nan)
    result = ranks.sub(1).div(scale, axis="index").mul(2).sub(1)
    single = counts.eq(1)
    if single.any():
        result.loc[single] = signal.loc[single].notna().astype(float).replace(0.0, np.nan)
        result.loc[single] = result.loc[single].replace(1.0, 0.0)
    return result


def select(
    values: pd.DataFrame,
    *,
    long_count: int = 1,
    short_count: int = 0,
) -> pd.DataFrame:
    """Select exact top and bottom asset counts at every timestamp.

    Ties are resolved stably by the input column order. Missing scores remain
    missing, selected assets become ``1`` or ``-1``, and other valid assets
    become ``0``.
    """
    signal = as_signal(values)
    if not isinstance(signal, pd.DataFrame):
        raise TypeError("values must be a time-by-asset pandas DataFrame")
    long_n = non_negative_integer(long_count, "long_count")
    short_n = non_negative_integer(short_count, "short_count")
    if long_n + short_n == 0:
        raise ValueError("at least one of long_count or short_count must be positive")

    result = pd.DataFrame(np.nan, index=signal.index, columns=signal.columns)
    for timestamp, row in signal.iterrows():
        valid = row.dropna()
        required = long_n + short_n
        if len(valid) < required:
            raise ValueError(
                f"timestamp {timestamp!r} has {len(valid)} valid assets; {required} required"
            )
        ordered = valid.sort_values(kind="stable")
        result.loc[timestamp, valid.index] = 0.0
        if short_n:
            result.loc[timestamp, ordered.index[:short_n]] = -1.0
        if long_n:
            result.loc[timestamp, ordered.index[-long_n:]] = 1.0
    return result


def neutralize(
    values: pd.DataFrame,
    exposures: pd.Series | pd.DataFrame,
    *,
    weights: pd.Series | None = None,
    add_intercept: bool = True,
) -> pd.DataFrame:
    """Remove static asset exposures from every signal timestamp.

    This is the time-panel signal adapter over `q.cross_section.neutralize`.
    Exposure and optional weight indexes must exactly match the signal's asset
    columns.
    """
    signal = as_signal(values)
    if not isinstance(signal, pd.DataFrame):
        raise TypeError("values must be a time-by-asset pandas DataFrame")
    if not isinstance(exposures, (pd.Series, pd.DataFrame)):
        raise TypeError("exposures must be a pandas Series or DataFrame")
    if not signal.columns.equals(exposures.index):
        raise ValueError("exposures index must exactly match signal columns")
    if weights is not None and not signal.columns.equals(weights.index):
        raise ValueError("weights index must exactly match signal columns")
    rows = [
        _neutralize_snapshot(
            row,
            exposures,
            weights=weights,
            add_intercept=add_intercept,
        )
        for _, row in signal.iterrows()
    ]
    return pd.DataFrame(rows, index=signal.index, columns=signal.columns)


def combine(
    signals: Sequence[SignalLike],
    *,
    weights: Sequence[float] | None = None,
) -> SignalLike:
    """Return the aligned weighted mean of multiple signal objects.

    Inputs must have exactly matching types and labels. Missing inputs are
    ignored per cell and the available non-negative weights are renormalized.
    """
    if not isinstance(signals, Sequence) or isinstance(signals, (str, bytes)):
        raise TypeError("signals must be a sequence of signal objects")
    if not signals:
        raise ValueError("signals must not be empty")
    validated = [as_signal(signal) for signal in signals]
    first = validated[0]
    for signal in validated[1:]:
        if type(signal) is not type(first):
            raise TypeError("signals must all have the same pandas type")
        if not signal.index.equals(first.index):
            raise ValueError("signals must have exactly matching indexes")
        if isinstance(first, pd.DataFrame) and not signal.columns.equals(first.columns):
            raise ValueError("signals must have exactly matching columns")
    if weights is None:
        weight_array = np.ones(len(validated), dtype=float)
    else:
        if len(weights) != len(validated):
            raise ValueError("weights length must match signals length")
        weight_array = np.asarray(weights, dtype=float)
        if not np.isfinite(weight_array).all() or (weight_array < 0).any():
            raise ValueError("weights must be finite and non-negative")
        if weight_array.sum() <= 0:
            raise ValueError("weights must contain at least one positive value")

    arrays = np.stack([signal.to_numpy(dtype=float) for signal in validated])
    available = ~np.isnan(arrays)
    shape = (len(weight_array),) + (1,) * (arrays.ndim - 1)
    expanded_weights = weight_array.reshape(shape)
    numerator = np.nansum(arrays * expanded_weights, axis=0)
    denominator = np.sum(available * expanded_weights, axis=0)
    combined = np.divide(
        numerator,
        denominator,
        out=np.full_like(numerator, np.nan, dtype=float),
        where=denominator > 0,
    )
    if isinstance(first, pd.Series):
        names = {signal.name for signal in validated}
        name = first.name if len(names) == 1 else "signal"
        return pd.Series(combined, index=first.index, name=name)
    return pd.DataFrame(combined, index=first.index, columns=first.columns)