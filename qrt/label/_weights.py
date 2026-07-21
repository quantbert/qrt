"""Sample uniqueness and weighting from overlapping label intervals."""

from __future__ import annotations

from numbers import Integral

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix

from qrt.label._validation import (
    non_negative_number,
    numeric_series,
    validate_index,
)


def _interval_positions(
    observations: pd.Index,
    end_times: pd.Series,
) -> tuple[np.ndarray, np.ndarray, pd.Index]:
    validate_index(observations, "observations")
    if not isinstance(end_times, pd.Series):
        raise TypeError("end_times must be a pandas Series")
    validate_index(end_times.index, "end_times index")
    if end_times.isna().any():
        raise ValueError("end_times must not contain missing values")

    events = end_times.index
    starts = observations.get_indexer(events)
    ends = observations.get_indexer(pd.Index(end_times.to_list()))
    if (starts < 0).any():
        raise ValueError("every event must be present in observations")
    if (ends < 0).any():
        raise ValueError("every end time must be present in observations")
    if (ends < starts).any():
        raise ValueError("every end time must be at or after its event")
    return starts, ends, events.rename("event_time")


def concurrency(observations: pd.Index, end_times: pd.Series) -> pd.Series:
    """Count active label intervals at every observation.

    Event intervals include both their start and end observations.

    Args:
        observations: Ordered, unique observation index.
        end_times: Series indexed by event start and containing inclusive event
            end times.

    Returns:
        Integer Series aligned to ``observations``.
    """
    starts, ends, _ = _interval_positions(observations, end_times)
    changes = np.zeros(len(observations) + 1, dtype=np.int64)
    np.add.at(changes, starts, 1)
    np.add.at(changes, ends + 1, -1)
    return pd.Series(
        np.cumsum(changes[:-1]),
        index=observations,
        name="concurrency",
    )


def indicator_matrix(
    observations: pd.Index,
    end_times: pd.Series,
) -> pd.DataFrame:
    """Build a sparse observation-by-event membership matrix.

    A value of 1 means the observation belongs to the event's inclusive
    lifetime. Summing rows therefore reproduces :func:`concurrency`, while
    summing inverse row counts over columns supports uniqueness calculations.

    Args:
        observations: Ordered, unique observation index.
        end_times: Series indexed by event start and containing inclusive event
            end times.

    Returns:
        Sparse integer DataFrame with observations as rows and event starts as
        columns.
    """
    starts, ends, events = _interval_positions(observations, end_times)
    lengths = ends - starts + 1
    columns = np.repeat(np.arange(len(events)), lengths)
    rows = np.concatenate(
        [np.arange(start, end + 1) for start, end in zip(starts, ends, strict=True)]
    ) if len(events) else np.array([], dtype=int)
    matrix = csc_matrix(
        (np.ones(len(rows), dtype=np.int8), (rows, columns)),
        shape=(len(observations), len(events)),
    )
    return pd.DataFrame.sparse.from_spmatrix(
        matrix,
        index=observations,
        columns=events,
    )


def purging_metadata(
    observations: pd.Index,
    end_times: pd.Series,
    *,
    embargo: int = 0,
) -> pd.DataFrame:
    """Export event-lifetime metadata for leakage-aware splitters.

    ``max_end_time`` is the latest endpoint among the current and all earlier
    events. A chronological training block ending at that row can only be
    followed safely at ``next_safe_time`` after also skipping ``embargo``
    observations. Missing safe times mean the required point lies beyond the
    available timeline.

    Args:
        observations: Ordered, unique observation index.
        end_times: Series indexed by event start and containing inclusive event
            end times.
        embargo: Non-negative number of observations to skip after the running
            maximum label end.

    Returns:
        Event-indexed DataFrame containing endpoint positions and labels,
        running maximum endpoints, prior-overlap flags, and next safe points.
    """
    if (
        not isinstance(embargo, Integral)
        or isinstance(embargo, bool)
        or embargo < 0
    ):
        raise ValueError("embargo must be a non-negative integer")
    starts, ends, events = _interval_positions(observations, end_times)
    running_ends = np.maximum.accumulate(ends) if len(ends) else ends.copy()
    previous_ends = np.r_[-1, running_ends[:-1]]
    safe_positions = running_ends + int(embargo) + 1
    valid_safe = safe_positions < len(observations)
    safe_values = [
        observations[position] if valid else pd.NA
        for position, valid in zip(safe_positions, valid_safe, strict=True)
    ]
    try:
        safe_times = pd.array(safe_values, dtype=observations.dtype)
    except (TypeError, ValueError):
        if pd.api.types.is_integer_dtype(observations.dtype):
            nullable_dtype = (
                "UInt64"
                if pd.api.types.is_unsigned_integer_dtype(observations.dtype)
                else "Int64"
            )
            safe_times = pd.array(safe_values, dtype=nullable_dtype)
        else:
            safe_times = pd.array(safe_values)

    return pd.DataFrame(
        {
            "end_time": end_times.reindex(events).array,
            "start_position": starts,
            "end_position": ends,
            "max_end_time": observations.take(running_ends),
            "max_end_position": running_ends,
            "overlaps_previous": starts <= previous_ends,
            "next_safe_time": safe_times,
            "next_safe_position": pd.array(
                [
                    int(position) if valid else pd.NA
                    for position, valid in zip(
                        safe_positions,
                        valid_safe,
                        strict=True,
                    )
                ],
                dtype="Int64",
            ),
        },
        index=events,
    )


def sequential_bootstrap(
    observations: pd.Index,
    end_times: pd.Series,
    *,
    size: int | None = None,
    random_state: int | np.random.Generator | None = None,
) -> pd.Index:
    """Draw events sequentially in proportion to marginal uniqueness.

    After every draw, candidate probabilities are recomputed from the average
    inverse concurrency that each event would have if selected next. Events may
    be drawn repeatedly, as in an ordinary bootstrap, while isolated or
    underrepresented lifetimes receive higher probability.

    Args:
        observations: Ordered, unique observation index.
        end_times: Series indexed by event start and containing inclusive event
            end times.
        size: Number of events to draw. Defaults to the original event count.
        random_state: Seed or NumPy random generator for reproducible draws.

    Returns:
        Index of sampled event starts, potentially containing duplicates.
    """
    _, _, events = _interval_positions(observations, end_times)
    if size is None:
        sample_size = len(events)
    elif not isinstance(size, Integral) or isinstance(size, bool) or size < 0:
        raise ValueError("size must be a non-negative integer")
    else:
        sample_size = int(size)
    if sample_size > 0 and len(events) == 0:
        raise ValueError("cannot sample from an empty event set")
    if isinstance(random_state, np.random.Generator):
        generator = random_state
    else:
        if isinstance(random_state, bool):
            raise TypeError("random_state must be an integer, Generator, or None")
        generator = np.random.default_rng(random_state)
    if sample_size == 0:
        return events.copy()

    membership = indicator_matrix(observations, end_times).sparse.to_coo().tocsc()
    active_counts = np.zeros(len(observations), dtype=np.int64)
    event_lengths = np.asarray(membership.sum(axis=0)).ravel()
    draws = np.empty(sample_size, dtype=np.int64)

    for draw in range(sample_size):
        inverse_concurrency = 1.0 / (active_counts + 1)
        marginal_uniqueness = (
            np.asarray(membership.T @ inverse_concurrency).ravel() / event_lengths
        )
        probabilities = marginal_uniqueness / marginal_uniqueness.sum()
        selected = int(generator.choice(len(events), p=probabilities))
        draws[draw] = selected
        start = membership.indptr[selected]
        stop = membership.indptr[selected + 1]
        active_counts[membership.indices[start:stop]] += 1

    return events.take(draws)


def average_uniqueness(
    observations: pd.Index,
    end_times: pd.Series,
    *,
    concurrency_counts: pd.Series | None = None,
) -> pd.Series:
    """Compute each label's mean inverse concurrency.

    Args:
        observations: Ordered, unique observation index.
        end_times: Series indexed by event start and containing inclusive end
            times.
        concurrency_counts: Optional precomputed output from
            :func:`concurrency`.

    Returns:
        Event-indexed Series in the interval (0, 1].

    Notes:
        Precomputed concurrency may be zero outside all event lifetimes, but it
        must be positive at every observation belonging to an event.
    """
    starts, ends, events = _interval_positions(observations, end_times)
    if concurrency_counts is None:
        counts = concurrency(observations, end_times)
    else:
        counts = numeric_series(concurrency_counts, "concurrency_counts")
        if not counts.index.equals(observations):
            raise ValueError("concurrency_counts index must match observations")
        if (counts < 0).any():
            raise ValueError("concurrency_counts must be non-negative")

    values = counts.to_numpy()
    uniqueness = np.empty(len(events), dtype=float)
    for offset, (start, end) in enumerate(zip(starts, ends, strict=True)):
        active_counts = values[start : end + 1]
        if (active_counts <= 0).any():
            raise ValueError("concurrency_counts must be positive within every event")
        uniqueness[offset] = np.mean(1.0 / active_counts)
    return pd.Series(uniqueness, index=events, name="average_uniqueness")


def sample_weights(
    prices: pd.Series,
    end_times: pd.Series,
    *,
    normalize: bool = True,
) -> pd.Series:
    """Weight labels by absolute return attributed through concurrency.

    Each log return is divided by the number of labels active at that
    observation before it is accumulated over an event's lifetime. Optional
    normalization scales nonzero weights to sum to the number of events.

    Args:
        prices: Ordered positive prices aligned to the labeling timeline.
        end_times: Series indexed by event start and containing inclusive end
            times, such as ``triple_barrier(...)["touch_time"]``.
        normalize: Scale weights to have unit mean when their sum is nonzero.

    Returns:
        Non-negative event-indexed sample weights.
    """
    if not isinstance(normalize, bool):
        raise TypeError("normalize must be a boolean")
    close = numeric_series(prices, "prices", positive=True)
    starts, ends, events = _interval_positions(close.index, end_times)
    counts = concurrency(close.index, end_times).to_numpy(dtype=float)
    log_returns = np.log(close).diff().fillna(0.0).to_numpy()
    attributed = np.divide(
        log_returns,
        counts,
        out=np.zeros_like(log_returns),
        where=counts > 0,
    )

    weights = np.empty(len(events), dtype=float)
    for offset, (start, end) in enumerate(zip(starts, ends, strict=True)):
        weights[offset] = abs(float(attributed[start : end + 1].sum()))
    if normalize and weights.sum() > 0:
        weights *= len(weights) / weights.sum()
    return pd.Series(weights, index=events, name="sample_weight")


def time_decay(
    weights: pd.Series,
    *,
    minimum_weight: float = 0.0,
) -> pd.Series:
    """Create linear recency factors from cumulative sample importance.

    The ordered input commonly contains average uniqueness. Its cumulative
    mass defines progress through the sample: the factor starts at
    ``minimum_weight`` before the oldest mass and reaches 1 at the newest
    event. Multiplying these factors into other sample weights gradually
    reduces older observations without deleting them.

    Args:
        weights: Ordered, non-negative event importance values.
        minimum_weight: Decay intercept in the closed interval [0, 1].

    Returns:
        Event-indexed factors between ``minimum_weight`` and 1.
    """
    importance = numeric_series(weights, "weights")
    if (importance < 0).any():
        raise ValueError("weights must be non-negative")
    minimum = non_negative_number(minimum_weight, "minimum_weight")
    if minimum > 1:
        raise ValueError("minimum_weight must be less than or equal to 1")
    total = float(importance.sum())
    if total <= 0:
        raise ValueError("weights must contain at least one positive value")

    progress = importance.cumsum() / total
    factors = minimum + (1.0 - minimum) * progress
    return factors.rename("time_decay")


def class_balance_weights(labels: pd.Series) -> pd.Series:
    """Give every observed class equal total sample weight.

    Args:
        labels: Ordered target labels without missing values.

    Returns:
        Event-indexed inverse-frequency factors normalized to unit mean.
        Empty input produces an empty Series.
    """
    if not isinstance(labels, pd.Series):
        raise TypeError("labels must be a pandas Series")
    validate_index(labels.index, "labels index")
    if labels.isna().any():
        raise ValueError("labels must not contain missing values")
    if labels.empty:
        return pd.Series(index=labels.index, dtype=float, name="class_balance_weight")

    counts = labels.value_counts()
    class_count = len(counts)
    factors = labels.map(len(labels) / (class_count * counts)).astype(float)
    return factors.rename("class_balance_weight")


def combine_weights(
    *weights: pd.Series,
    normalize: bool = True,
) -> pd.Series:
    """Multiply aligned sample-weight components.

    Args:
        *weights: One or more non-negative Series with identical indexes.
        normalize: Scale a nonzero result to unit mean.

    Returns:
        Combined event-indexed sample weights.

    Notes:
        A zero in any component eliminates that event multiplicatively. When
        normalization is requested, an all-zero result is rejected because it
        cannot define usable training weights.
    """
    if not weights:
        raise ValueError("at least one weight Series is required")
    if not isinstance(normalize, bool):
        raise TypeError("normalize must be a boolean")

    components = [
        numeric_series(component, f"weights[{offset}]")
        for offset, component in enumerate(weights)
    ]
    index = components[0].index
    for component in components:
        if not component.index.equals(index):
            raise ValueError("every weight Series must have the same index")
        if (component < 0).any():
            raise ValueError("weight Series must be non-negative")

    combined = np.prod([component.to_numpy() for component in components], axis=0)
    if normalize and len(combined):
        total = float(combined.sum())
        if total <= 0:
            raise ValueError("combined weights must contain a positive value")
        combined *= len(combined) / total
    return pd.Series(combined, index=index, name="sample_weight")