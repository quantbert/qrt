"""Aligned machine-learning datasets and split metadata."""

import warnings
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Protocol

import joblib
import pandas as pd

Target = pd.Series | pd.DataFrame
_COMPONENTS = ("X", "y", "sample_weight", "metadata")


def _to_pandas(
    components: Mapping[str, pd.Series | pd.DataFrame | None],
    selected: str | Sequence[str],
    *,
    start: Any = None,
    end: Any = None,
) -> pd.DataFrame:
    names = (selected,) if isinstance(selected, str) else tuple(selected)
    if not names:
        raise ValueError("components must contain at least one component name")
    unknown = set(names) - set(_COMPONENTS)
    if unknown:
        raise ValueError(f"unknown dataset components: {sorted(unknown)}")

    frames = []
    for name in names:
        value = components[name]
        if value is None:
            continue
        if isinstance(value, pd.Series):
            value = value.to_frame(name=value.name or name)
        frames.append(value)
    if not frames:
        raise ValueError("none of the selected components are present")

    result = pd.concat(frames, axis="columns", sort=False)
    duplicates = result.columns[result.columns.duplicated()].unique().tolist()
    if duplicates:
        raise ValueError(f"dataset components contain duplicate columns: {duplicates}")
    return result.loc[start:end]


def _frozen_mapping(values: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(values))


@dataclass(frozen=True)
class Partition:
    """A named subset and its role in model fitting or evaluation."""

    name: str
    role: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("partition name must not be empty")
        if not self.role:
            raise ValueError("partition role must not be empty")
        object.__setattr__(self, "metadata", _frozen_mapping(self.metadata))


@dataclass(frozen=True)
class Split:
    """One assignment of dataset rows to named partitions."""

    membership: pd.Series
    partitions: Sequence[Partition]
    name: str = "default"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("split name must not be empty")
        if not isinstance(self.membership, pd.Series):
            raise TypeError("split membership must be a pandas Series")
        if self.membership.isna().any():
            raise ValueError("split membership must assign every row")
        partitions = tuple(self.partitions)
        if not partitions:
            raise ValueError("split must define at least one partition")
        names = [partition.name for partition in partitions]
        if len(names) != len(set(names)):
            raise ValueError("partition names must be unique within a split")
        unknown = set(self.membership.unique()) - set(names)
        if unknown:
            raise ValueError(f"split membership contains unknown partitions: {sorted(unknown)}")
        object.__setattr__(self, "membership", self.membership.copy())
        object.__setattr__(self, "partitions", partitions)
        object.__setattr__(self, "metadata", _frozen_mapping(self.metadata))

    def partition(self, name: str) -> Partition:
        """Return one partition definition by name."""
        for partition in self.partitions:
            if partition.name == name:
                return partition
        raise KeyError(f"unknown partition {name!r}")

    @property
    def fit_partitions(self) -> tuple[str, ...]:
        """Return names of partitions from which learned state may be fitted."""
        return tuple(
            partition.name for partition in self.partitions if partition.role == "fit"
        )


@dataclass(frozen=True)
class SplitScheme:
    """A named collection of splits, such as the folds of walk-forward CV."""

    splits: Sequence[Split]
    name: str = "default"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("split scheme name must not be empty")
        splits = tuple(self.splits)
        if not splits:
            raise ValueError("split scheme must contain at least one split")
        names = [split.name for split in splits]
        if len(names) != len(set(names)):
            raise ValueError("split names must be unique within a scheme")
        object.__setattr__(self, "splits", splits)
        object.__setattr__(self, "metadata", _frozen_mapping(self.metadata))

    def split(self, fold: int | str = 0) -> Split:
        """Return a split by zero-based fold position or name."""
        if isinstance(fold, int):
            return self.splits[fold]
        for split in self.splits:
            if split.name == fold:
                return split
        raise KeyError(f"unknown split {fold!r}")

    def __iter__(self) -> Iterator[Split]:
        return iter(self.splits)

    def __len__(self) -> int:
        return len(self.splits)


class DatasetSplitter(Protocol):
    """Structural interface implemented by dataset splitters."""

    def split(self, dataset: "Dataset") -> Split | SplitScheme: ...


class DatasetView:
    """A partition-backed view over one aligned :class:`Dataset`."""

    def __init__(self, dataset: "Dataset", split: Split, partition: Partition) -> None:
        self.dataset = dataset
        self.split = split
        self.partition = partition

    @property
    def index(self) -> pd.Index:
        """Return row labels assigned to this partition."""
        return self.dataset.index[self.split.membership.eq(self.partition.name).to_numpy()]

    @property
    def X(self) -> pd.DataFrame:
        """Return feature rows assigned to this partition."""
        return self.dataset.X.loc[self.index]

    @property
    def y(self) -> Target | None:
        """Return target rows assigned to this partition, when present."""
        return None if self.dataset.y is None else self.dataset.y.loc[self.index]

    @property
    def sample_weight(self) -> pd.Series | None:
        """Return sample weights assigned to this partition, when present."""
        if self.dataset.sample_weight is None:
            return None
        return self.dataset.sample_weight.loc[self.index]

    @property
    def metadata(self) -> pd.DataFrame | None:
        """Return row metadata assigned to this partition, when present."""
        if self.dataset.metadata is None:
            return None
        return self.dataset.metadata.loc[self.index]

    def to_pandas(
        self,
        components: str | Sequence[str] = _COMPONENTS,
        *,
        start: Any = None,
        end: Any = None,
    ) -> pd.DataFrame:
        """Return selected partition components as one optionally bounded frame."""
        return _to_pandas(
            {
                "X": self.X,
                "y": self.y,
                "sample_weight": self.sample_weight,
                "metadata": self.metadata,
            },
            components,
            start=start,
            end=end,
        )

    def __len__(self) -> int:
        return int(self.split.membership.eq(self.partition.name).sum())


class Fold:
    """A dataset facade bound to one split within a split scheme."""

    def __init__(
        self,
        dataset: "Dataset",
        scheme: SplitScheme,
        split: Split,
    ) -> None:
        self.dataset = dataset
        self.scheme = scheme
        self.split = split

    @property
    def name(self) -> str:
        """Return this fold's split name."""
        return self.split.name

    @property
    def X(self) -> pd.DataFrame:
        """Return the complete feature frame governed by this fold."""
        return self.dataset.X

    @property
    def y(self) -> Target | None:
        """Return the complete aligned target governed by this fold."""
        return self.dataset.y

    @property
    def sample_weight(self) -> pd.Series | None:
        """Return the complete aligned sample weights governed by this fold."""
        return self.dataset.sample_weight

    @property
    def metadata(self) -> pd.DataFrame | None:
        """Return the complete row metadata governed by this fold."""
        return self.dataset.metadata

    @property
    def index(self) -> pd.Index:
        """Return the parent dataset's canonical row index."""
        return self.dataset.index

    @property
    def is_split(self) -> bool:
        """Return ``True`` because this facade is bound to one split."""
        return True

    @property
    def partitions(self) -> Mapping[str, DatasetView]:
        """Return named partition views for this fold."""
        return MappingProxyType(
            {
                partition.name: DatasetView(self.dataset, self.split, partition)
                for partition in self.split.partitions
            }
        )

    def partition(self, name: str) -> DatasetView:
        """Return one named partition view from this fold."""
        return DatasetView(self.dataset, self.split, self.split.partition(name))

    @property
    def train(self) -> DatasetView:
        """Return this fold's conventional ``train`` partition."""
        return self.partition("train")

    @property
    def validation(self) -> DatasetView:
        """Return this fold's conventional ``validation`` partition."""
        return self.partition("validation")

    @property
    def test(self) -> DatasetView:
        """Return this fold's conventional ``test`` partition."""
        return self.partition("test")

    def __getitem__(self, name: str) -> DatasetView:
        return self.partition(name)

    def __len__(self) -> int:
        return len(self.dataset)


class _BoundSplitScheme:
    """A split scheme whose iteration produces dataset-bound folds."""

    def __init__(self, dataset: "Dataset", scheme: SplitScheme) -> None:
        self.dataset = dataset
        self.scheme = scheme

    @property
    def name(self) -> str:
        return self.scheme.name

    @property
    def metadata(self) -> Mapping[str, Any]:
        return self.scheme.metadata

    @property
    def splits(self) -> Sequence[Split]:
        return self.scheme.splits

    def split(self, fold: int | str = 0) -> Split:
        """Return the raw split definition by position or name."""
        return self.scheme.split(fold)

    def fold(self, fold: int | str = 0) -> Fold:
        """Return a dataset facade bound to one split."""
        return Fold(self.dataset, self.scheme, self.scheme.split(fold))

    def __iter__(self) -> Iterator[Fold]:
        for split in self.scheme:
            yield Fold(self.dataset, self.scheme, split)

    def __getitem__(self, fold: int | str) -> Fold:
        return self.fold(fold)

    def __len__(self) -> int:
        return len(self.scheme)


class Dataset:
    """One aligned collection of model inputs, targets, weights, and metadata.

    The pandas index is the dataset's row identity: ``X``, ``y``,
    ``sample_weight``, and ``metadata`` must describe the same indexed rows.
    When ``on`` is provided, each component must expose those keys either as
    DataFrame columns or as its complete named index. Key columns become the
    canonical dataset index, and component rows are reordered to ``X`` order.
    """

    def __init__(
        self,
        X: pd.DataFrame,
        y: Target | None = None,
        sample_weight: pd.Series | None = None,
        metadata: pd.DataFrame | None = None,
        *,
        on: str | Sequence[str] | None = None,
        splits: Mapping[str, SplitScheme | _BoundSplitScheme] | None = None,
    ) -> None:
        if not isinstance(X, pd.DataFrame):
            raise TypeError("X must be a pandas DataFrame")
        if on is not None:
            keys = (on,) if isinstance(on, str) else tuple(on)
            if not keys or any(not isinstance(key, str) or not key for key in keys):
                raise ValueError("on must contain at least one non-empty key name")
            if len(keys) != len(set(keys)):
                raise ValueError("on key names must be unique")

            X = _with_key_index("X", X, keys)
            y = _align_on_keys("y", y, keys, X.index)
            sample_weight = _align_on_keys(
                "sample_weight", sample_weight, keys, X.index
            )
            metadata = _align_on_keys("metadata", metadata, keys, X.index)
        if not X.index.is_unique:
            raise ValueError("dataset index must be unique")
        self.X = X
        self.y = self._validate_aligned("y", y, (pd.Series, pd.DataFrame))
        self.sample_weight = self._validate_aligned(
            "sample_weight", sample_weight, (pd.Series,)
        )
        self.metadata = self._validate_aligned("metadata", metadata, (pd.DataFrame,))
        schemes = {}
        for name, candidate in dict(splits or {}).items():
            scheme = (
                candidate.scheme
                if isinstance(candidate, _BoundSplitScheme)
                else candidate
            )
            if not isinstance(scheme, SplitScheme):
                raise TypeError("splits must contain SplitScheme values")
            if name != scheme.name:
                raise ValueError("split scheme mapping keys must match scheme names")
            for split in scheme.splits:
                self._validate_index("split membership", split.membership.index)
            schemes[name] = scheme
        self._split_schemes = MappingProxyType(schemes)
        self.splits = MappingProxyType(
            {
                name: _BoundSplitScheme(self, scheme)
                for name, scheme in schemes.items()
            }
        )

    @property
    def index(self) -> pd.Index:
        """Return the canonical row index shared by every dataset component."""
        return self.X.index

    @property
    def is_split(self) -> bool:
        """Return whether at least one split scheme is attached."""
        return bool(self.splits)

    def to_pandas(
        self,
        components: str | Sequence[str] = _COMPONENTS,
        *,
        start: Any = None,
        end: Any = None,
    ) -> pd.DataFrame:
        """Return selected aligned components as one optionally bounded frame."""
        return _to_pandas(
            {
                "X": self.X,
                "y": self.y,
                "sample_weight": self.sample_weight,
                "metadata": self.metadata,
            },
            components,
            start=start,
            end=end,
        )

    def _validate_index(self, name: str, index: pd.Index) -> None:
        if not index.equals(self.index):
            raise ValueError(f"{name} must have exactly the same index as X")

    def _validate_aligned(self, name: str, value: Any, types: tuple[type, ...]):
        if value is None:
            return None
        if not isinstance(value, types):
            expected = " or ".join(item.__name__ for item in types)
            raise TypeError(f"{name} must be a pandas {expected}")
        self._validate_index(name, value.index)
        return value

    def with_split(self, split: Split | SplitScheme) -> "Dataset":
        """Return a dataset sharing the same data with an added split scheme."""
        scheme = (
            split
            if isinstance(split, SplitScheme)
            else SplitScheme([split], name="default")
        )
        schemes = dict(self._split_schemes)
        schemes[scheme.name] = scheme
        return Dataset(
            self.X,
            self.y,
            self.sample_weight,
            self.metadata,
            splits=schemes,
        )

    def split(self, splitter: DatasetSplitter) -> "Dataset":
        """Return a dataset with the split or scheme produced by ``splitter``."""
        result = splitter.split(self)
        if not isinstance(result, (Split, SplitScheme)):
            raise TypeError("splitter.split() must return a Split or SplitScheme")
        return self.with_split(result)

    def save(self, path: str | Path) -> None:
        """Serialize the aligned dataset and all split metadata with joblib."""
        schemes = []
        for scheme in self.splits.values():
            splits = []
            for split in scheme.splits:
                splits.append(
                    {
                        "membership": split.membership,
                        "partitions": [
                            {
                                "name": partition.name,
                                "role": partition.role,
                                "metadata": dict(partition.metadata),
                            }
                            for partition in split.partitions
                        ],
                        "name": split.name,
                        "metadata": dict(split.metadata),
                    }
                )
            schemes.append(
                {
                    "name": scheme.name,
                    "metadata": dict(scheme.metadata),
                    "splits": splits,
                }
            )
        joblib.dump(
            {
                "X": self.X,
                "y": self.y,
                "sample_weight": self.sample_weight,
                "metadata": self.metadata,
                "schemes": schemes,
            },
            path,
        )

    @classmethod
    def load(cls, path: str | Path) -> "Dataset":
        """Load a dataset written by :meth:`save`.

        Only load files from trusted sources because joblib uses pickle.
        """
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Setting the shape on a NumPy array has been deprecated",
                category=DeprecationWarning,
                module=r"joblib\.numpy_pickle",
            )
            payload = joblib.load(path)
        if not isinstance(payload, dict) or "X" not in payload:
            raise TypeError("serialized object is not a Dataset payload")
        schemes = {}
        for scheme_data in payload.get("schemes", []):
            splits = []
            for split_data in scheme_data["splits"]:
                partitions = [Partition(**item) for item in split_data["partitions"]]
                splits.append(
                    Split(
                        split_data["membership"],
                        partitions,
                        name=split_data["name"],
                        metadata=split_data["metadata"],
                    )
                )
            scheme = SplitScheme(
                splits,
                name=scheme_data["name"],
                metadata=scheme_data["metadata"],
            )
            schemes[scheme.name] = scheme
        return cls(
            payload["X"],
            payload.get("y"),
            payload.get("sample_weight"),
            payload.get("metadata"),
            splits=schemes,
        )

    def partition(
        self,
        name: str,
        *,
        scheme: str = "default",
        fold: int | str = 0,
    ) -> DatasetView:
        """Return a row view for one partition in one split scheme."""
        if scheme not in self.splits:
            raise KeyError(f"unknown split scheme {scheme!r}")
        split = self.splits[scheme].split(fold)
        return DatasetView(self, split, split.partition(name))

    def fold(
        self,
        scheme: str,
        fold: int | str = 0,
    ) -> Fold:
        """Return a dataset facade bound to one fold in ``scheme``."""
        if scheme not in self.splits:
            raise KeyError(f"unknown split scheme {scheme!r}")
        return self.splits[scheme].fold(fold)

    @property
    def partitions(self) -> Mapping[str, DatasetView]:
        """Return named views from the first split of the default scheme."""
        return self.fold("default").partitions

    @property
    def train(self) -> DatasetView:
        """Return the default split's conventional ``train`` partition."""
        return self.partition("train")

    @property
    def validation(self) -> DatasetView:
        """Return the default split's conventional ``validation`` partition."""
        return self.partition("validation")

    @property
    def test(self) -> DatasetView:
        """Return the default split's conventional ``test`` partition."""
        return self.partition("test")

    def __getitem__(self, name: str) -> DatasetView:
        return self.partition(name)

    def __len__(self) -> int:
        return len(self.X)


def _with_key_index(
    name: str,
    value: pd.Series | pd.DataFrame,
    keys: tuple[str, ...],
) -> pd.Series | pd.DataFrame:
    if isinstance(value, pd.DataFrame) and all(key in value.columns for key in keys):
        keyed = value.set_index(list(keys))
    elif tuple(value.index.names) == keys:
        keyed = value.copy()
    else:
        raise ValueError(
            f"{name} must contain key columns {list(keys)!r} or use them as its index"
        )
    if not keyed.index.is_unique:
        raise ValueError(f"{name} keys must be unique")
    return keyed


def _align_on_keys(
    name: str,
    value: pd.Series | pd.DataFrame | None,
    keys: tuple[str, ...],
    index: pd.Index,
) -> pd.Series | pd.DataFrame | None:
    if value is None:
        return None
    keyed = _with_key_index(name, value, keys)
    if len(index.difference(keyed.index)) or len(keyed.index.difference(index)):
        raise ValueError(f"{name} keys must exactly match feature keys")
    return keyed.reindex(index)