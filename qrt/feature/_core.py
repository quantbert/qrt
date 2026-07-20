"""Feature definitions, computation, and materialization."""

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Protocol

import numpy as np
import pandas as pd

FeatureFunction = Callable[..., pd.Series]


class FeatureSink(Protocol):
    """Persistence target accepted by :func:`materialize`."""

    def write(self, data: pd.DataFrame, *, table: str) -> None: ...


@dataclass(frozen=True)
class Feature:
    """One reproducible, scalar feature definition.

    Args:
        name: Stable output-column name.
        function: Callable returning one Series.
        inputs: Mapping from callable argument names to source columns.
        params: Fixed keyword arguments passed to ``function``.
        entity_keys: Columns that identify independent entities. Computation is
            applied separately to each entity to prevent history leakage.
        timestamp: Column defining observation order and feature availability.
        version: Definition version stored alongside the feature name.
        lookback: Required history in rows, when known.
        available_at: Human-readable availability boundary such as
            ``"bar_close"``. This is metadata, not a scheduling instruction.
    """

    name: str
    function: FeatureFunction
    inputs: Mapping[str, str]
    params: Mapping[str, Any] = field(default_factory=dict)
    entity_keys: tuple[str, ...] = ("symbol",)
    timestamp: str = "datetime"
    version: str = "1"
    lookback: int | None = None
    available_at: str | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("feature name must not be empty")
        if not callable(self.function):
            raise TypeError("feature function must be callable")
        if not self.inputs:
            raise ValueError("feature inputs must not be empty")
        if not self.timestamp:
            raise ValueError("feature timestamp must not be empty")
        if not self.version:
            raise ValueError("feature version must not be empty")
        if self.lookback is not None and self.lookback < 0:
            raise ValueError("feature lookback must be non-negative")
        if set(self.inputs) & set(self.params):
            overlap = sorted(set(self.inputs) & set(self.params))
            raise ValueError(f"feature inputs and params overlap: {overlap}")
        object.__setattr__(self, "inputs", MappingProxyType(dict(self.inputs)))
        object.__setattr__(self, "params", MappingProxyType(dict(self.params)))
        object.__setattr__(self, "entity_keys", tuple(self.entity_keys))

    @property
    def identity(self) -> str:
        """Return the stable ``name:version`` identity."""
        return f"{self.name}:{self.version}"


class FeatureSet:
    """Features sharing one entity and timestamp contract."""

    def __init__(
        self,
        features: Iterable[Feature],
        *,
        name: str = "default",
        version: str = "1",
    ) -> None:
        self.features = tuple(features)
        if not self.features:
            raise ValueError("feature set must contain at least one feature")
        if not name or not version:
            raise ValueError("feature set name and version must not be empty")
        names = [feature.name for feature in self.features]
        if len(names) != len(set(names)):
            raise ValueError("feature names must be unique within a feature set")
        contracts = {
            (feature.entity_keys, feature.timestamp) for feature in self.features
        }
        if len(contracts) != 1:
            raise ValueError(
                "all features in a feature set must share entity_keys and timestamp"
            )
        self.name = name
        self.version = version
        self.entity_keys = self.features[0].entity_keys
        self.timestamp = self.features[0].timestamp

    def __iter__(self):
        return iter(self.features)

    def __len__(self) -> int:
        return len(self.features)


def _validate_source(data: pd.DataFrame, features: FeatureSet) -> None:
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame")
    required = {
        features.timestamp,
        *features.entity_keys,
        *(column for feature in features for column in feature.inputs.values()),
    }
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"data is missing required columns: {missing}")
    if data[list(features.entity_keys) + [features.timestamp]].isna().any().any():
        raise ValueError("entity keys and timestamp must not contain missing values")


def _groups(data: pd.DataFrame, features: FeatureSet) -> list[np.ndarray]:
    if not features.entity_keys:
        return [np.arange(len(data))]
    grouped = data.groupby(
        list(features.entity_keys), sort=False, observed=True, dropna=False
    )
    return [np.asarray(positions) for positions in grouped.indices.values()]


def _compute_one(
    feature: Feature,
    data: pd.DataFrame,
    groups: list[np.ndarray],
) -> pd.Series:
    output = pd.Series(index=data.index, dtype="object", name=feature.name)
    for positions in groups:
        group = data.iloc[positions]
        if not group[feature.timestamp].is_monotonic_increasing:
            raise ValueError(
                f"data must be ordered by {feature.timestamp!r} within each entity"
            )
        kwargs = {
            argument: group[column]
            for argument, column in feature.inputs.items()
        }
        result = feature.function(**kwargs, **feature.params)
        if not isinstance(result, pd.Series):
            raise TypeError(
                f"feature {feature.name!r} must return a pandas Series"
            )
        if not result.index.equals(group.index):
            raise ValueError(
                f"feature {feature.name!r} must preserve the source index"
            )
        output.iloc[positions] = result.to_numpy()
    return output.infer_objects()


def compute(features: FeatureSet, data: pd.DataFrame) -> pd.DataFrame:
    """Compute a feature set without crossing entity boundaries.

    The source must already be ordered by timestamp within each entity. qrt
    validates this invariant instead of silently sorting database extracts.
    Entity and timestamp columns are retained for point-in-time persistence.
    """
    if not isinstance(features, FeatureSet):
        raise TypeError("features must be a FeatureSet")
    _validate_source(data, features)
    groups = _groups(data, features)
    keys = [*features.entity_keys, features.timestamp]
    result = data.loc[:, keys].copy()
    for feature in features:
        result[feature.name] = _compute_one(feature, data, groups)
    return result


def materialize(
    features: FeatureSet,
    data: pd.DataFrame,
    sink: FeatureSink,
    *,
    table: str,
) -> pd.DataFrame:
    """Compute a feature set and write it to a database-like sink."""
    result = compute(features, data)
    sink.write(result, table=table)
    return result