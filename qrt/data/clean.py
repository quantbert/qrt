"""Deterministic cleaning and validation for market-data frames."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Literal

import numpy as np
import pandas as pd

DuplicateKeep = Literal["first", "last", False]

_OHLCV_ALIASES = {
    "date": "datetime",
    "timestamp": "datetime",
    "ticker": "symbol",
    "adj_close": "adjusted_close",
    "adjclose": "adjusted_close",
}
_OHLCV_COLUMNS = ("open", "high", "low", "close", "volume")


def _canonical_name(name: object) -> object:
    if not isinstance(name, str):
        return name
    normalized = name.strip().lower().replace(" ", "_").replace("-", "_")
    return _OHLCV_ALIASES.get(normalized, normalized)


def _timestamp_values(data: pd.DataFrame, timestamp: str) -> pd.Series:
    if timestamp in data.columns:
        return data[timestamp]
    if data.index.name == timestamp:
        return pd.Series(data.index, index=data.index, name=timestamp)
    raise ValueError(f"data must contain {timestamp!r} as a column or index")


def _normalize_datetime(
    values: pd.Series | pd.Index,
    *,
    timezone: str | None,
    ambiguous: str,
    nonexistent: str,
) -> pd.DatetimeIndex:
    parsed = pd.DatetimeIndex(pd.to_datetime(values, errors="raise"))
    if timezone is None:
        return parsed
    if parsed.tz is None:
        return parsed.tz_localize(
            timezone, ambiguous=ambiguous, nonexistent=nonexistent
        )
    return parsed.tz_convert(timezone)


def normalize_timestamps(
    data: pd.DataFrame,
    *,
    timestamp: str = "datetime",
    timezone: str | None = "UTC",
    ambiguous: str = "raise",
    nonexistent: str = "raise",
) -> pd.DataFrame:
    """Return a copy with a normalized datetime column or index.

    Naive timestamps are localized to ``timezone`` and timezone-aware values
    are converted to it. Pass ``timezone=None`` to retain naive timestamps.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame")
    result = data.copy()
    if timestamp in result.columns:
        normalized = _normalize_datetime(
            result[timestamp],
            timezone=timezone,
            ambiguous=ambiguous,
            nonexistent=nonexistent,
        )
        result[timestamp] = pd.Series(normalized, index=result.index)
    elif result.index.name == timestamp:
        result.index = _normalize_datetime(
            result.index,
            timezone=timezone,
            ambiguous=ambiguous,
            nonexistent=nonexistent,
        ).rename(timestamp)
    else:
        raise ValueError(f"data must contain {timestamp!r} as a column or index")
    return result


def deduplicate(
    data: pd.DataFrame,
    *,
    subset: Sequence[str] | None = None,
    keep: DuplicateKeep = "last",
) -> pd.DataFrame:
    """Return a copy with duplicate observations removed.

    By default, observations are identified by ``symbol`` when present and by
    the ``datetime`` column or index.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame")
    if keep not in {"first", "last", False}:
        raise ValueError("keep must be 'first', 'last', or False")
    if subset is None:
        subset = tuple(
            column
            for column in ("symbol", "datetime")
            if column in data.columns or data.index.name == column
        )
    if not subset:
        raise ValueError("subset must contain at least one key")
    missing = [
        column
        for column in subset
        if column not in data.columns and data.index.name != column
    ]
    if missing:
        raise ValueError(f"data is missing duplicate keys: {missing}")
    keys = pd.DataFrame(index=data.index)
    for column in subset:
        keys[column] = (
            data[column].to_numpy() if column in data.columns else data.index
        )
    return data.loc[~keys.duplicated(keep=keep).to_numpy()].copy()


def validate_ohlcv(
    data: pd.DataFrame,
    *,
    timestamp: str = "datetime",
    entity_keys: Sequence[str] = ("symbol",),
    allow_missing: bool = False,
) -> None:
    """Validate canonical OHLCV columns, ordering, and market invariants."""
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame")
    missing = sorted(set(_OHLCV_COLUMNS) - set(data.columns))
    if missing:
        raise ValueError(f"data is missing OHLCV columns: {missing}")
    missing_keys = sorted(set(entity_keys) - set(data.columns))
    if missing_keys:
        raise ValueError(f"data is missing entity keys: {missing_keys}")
    timestamps = _timestamp_values(data, timestamp)
    if timestamps.isna().any():
        raise ValueError("timestamps must not contain missing values")
    numeric = data.loc[:, _OHLCV_COLUMNS]
    if any(not pd.api.types.is_numeric_dtype(numeric[column]) for column in numeric):
        raise TypeError("OHLCV columns must be numeric")
    if not allow_missing and numeric.isna().any().any():
        raise ValueError("OHLCV columns must not contain missing values")
    finite = numeric.to_numpy(dtype=float)
    if not np.isfinite(finite[~np.isnan(finite)]).all():
        raise ValueError("OHLCV columns must contain only finite values")
    high_values = numeric[["high", "open", "close"]].dropna()
    if (high_values["high"] < high_values[["open", "close"]].max(axis=1)).any():
        raise ValueError("high must be at least open and close")
    low_values = numeric[["low", "open", "close"]].dropna()
    if (low_values["low"] > low_values[["open", "close"]].min(axis=1)).any():
        raise ValueError("low must be at most open and close")
    bounds = numeric[["high", "low"]].dropna()
    if (bounds["high"] < bounds["low"]).any():
        raise ValueError("high must be at least low")
    if (numeric["volume"].dropna() < 0).any():
        raise ValueError("volume must be non-negative")

    keys = [*entity_keys, timestamp]
    key_frame = data.reset_index() if timestamp == data.index.name else data
    if key_frame.duplicated(keys).any():
        raise ValueError("each entity and timestamp must identify at most one row")
    grouped = (
        key_frame.groupby(list(entity_keys), sort=False, observed=True, dropna=False)
        if entity_keys
        else [(None, key_frame)]
    )
    if any(not group[timestamp].is_monotonic_increasing for _, group in grouped):
        raise ValueError(f"data must be ordered by {timestamp!r} within each entity")


def detect_gaps(
    data: pd.DataFrame,
    frequency: str | pd.Timedelta,
    *,
    timestamp: str = "datetime",
    entity_keys: Sequence[str] = ("symbol",),
) -> pd.DataFrame:
    """Return one gap record per entity and pair of observed timestamps.

    Each record contains the entity keys, first and last missing timestamps,
    and number of missing periods at the requested regular frequency.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame")
    missing = sorted(set(entity_keys) - set(data.columns))
    if missing:
        raise ValueError(f"data is missing entity keys: {missing}")
    frame = data.copy()
    frame[timestamp] = _timestamp_values(data, timestamp).to_numpy()
    if not pd.api.types.is_datetime64_any_dtype(frame[timestamp].dtype):
        raise TypeError("timestamps must have a pandas datetime dtype")
    columns = [*entity_keys, "gap_start", "gap_end", "missing_count"]
    records: list[dict[str, object]] = []
    grouped = (
        frame.groupby(list(entity_keys), sort=False, observed=True, dropna=False)
        if entity_keys
        else [((), frame)]
    )
    for group_key, group in grouped:
        times = pd.DatetimeIndex(group[timestamp].drop_duplicates().sort_values())
        key_values = group_key if isinstance(group_key, tuple) else (group_key,)
        for previous, current in zip(times[:-1], times[1:], strict=True):
            missing_times = pd.date_range(
                previous, current, freq=frequency, inclusive="neither"
            )
            if len(missing_times):
                record = dict(zip(entity_keys, key_values, strict=True))
                record.update(
                    gap_start=missing_times[0],
                    gap_end=missing_times[-1],
                    missing_count=len(missing_times),
                )
                records.append(record)
    return pd.DataFrame.from_records(records, columns=columns)


def canonicalize_ohlcv(
    data: pd.DataFrame,
    *,
    column_map: Mapping[str, str] | None = None,
    timestamp: str = "datetime",
    entity_keys: Sequence[str] = ("symbol",),
    timezone: str | None = "UTC",
    duplicate_keep: DuplicateKeep = "last",
    allow_missing: bool = False,
) -> pd.DataFrame:
    """Canonicalize, order, deduplicate, and validate an OHLCV frame."""
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame")
    rename = {column: _canonical_name(column) for column in data.columns}
    if column_map:
        rename.update(column_map)
    result = data.rename(columns=rename).copy()
    result.index = result.index.rename(_canonical_name(result.index.name))
    if result.columns.has_duplicates:
        raise ValueError("canonical column names must be unique")
    for column in _OHLCV_COLUMNS:
        if column in result:
            result[column] = pd.to_numeric(result[column], errors="raise")
    result = normalize_timestamps(
        result, timestamp=timestamp, timezone=timezone
    )
    result = deduplicate(
        result, subset=(*entity_keys, timestamp), keep=duplicate_keep
    )
    if timestamp in result.columns:
        result = result.sort_values([*entity_keys, timestamp], kind="stable")
    else:
        result = result.sort_index(kind="stable")
    validate_ohlcv(
        result,
        timestamp=timestamp,
        entity_keys=entity_keys,
        allow_missing=allow_missing,
    )
    return result