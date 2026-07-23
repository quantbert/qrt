"""Temporal splitters that produce aligned :mod:`qrt.dataset` schemes."""

from dataclasses import dataclass
from math import isclose
from numbers import Integral, Real
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit as SklearnTimeSeriesSplit

from qrt.dataset._core import Dataset, Partition, Split, SplitScheme

_TRAIN = Partition("train", "fit")
_VALIDATION = Partition("validation", "evaluate")
_TEST = Partition("test", "holdout")
_EXCLUDED = Partition("excluded", "excluded")


def _ordered_index(dataset: Dataset) -> pd.Index:
    if not dataset.index.is_monotonic_increasing:
        raise ValueError("dataset index must be ordered for temporal splitting")
    return dataset.index


def _membership(index: pd.Index) -> pd.Series:
    return pd.Series("excluded", index=index, name="partition", dtype="object")


@dataclass(frozen=True)
class TemporalSplit:
    """Create one ordered train/validation/test assignment.

    Args:
        train_end: Inclusive end of the training partition. Alternatively, use
            the size arguments to assign partitions by row count or proportion.
        validation_end: Inclusive end of validation. Omit validation by leaving
            this as ``None``.
        test_end: Inclusive end of test. Rows after it are excluded. By default,
            test extends to the end of the dataset.
        name: Split name.
        train_size: Training row count or proportion.
        validation_size: Validation row count or proportion. Leaving it unset
            omits validation in size mode.
        test_size: Test row count or proportion. When either ``train_size`` or
            ``test_size`` is unset, it receives the remaining rows.
    """

    train_end: Any | None = None
    validation_end: Any | None = None
    test_end: Any | None = None
    name: str = "default"
    train_size: int | float | None = None
    validation_size: int | float | None = None
    test_size: int | float | None = None

    def split(self, dataset: Dataset) -> Split:
        """Return the ordered assignment for ``dataset``."""
        index = _ordered_index(dataset)
        sizes = (self.train_size, self.validation_size, self.test_size)
        if any(size is not None for size in sizes):
            if any(
                boundary is not None
                for boundary in (self.train_end, self.validation_end, self.test_end)
            ):
                raise ValueError("boundaries and sizes cannot be combined")
            return self._split_by_size(index)
        if self.train_end is None:
            raise ValueError("train_end or train_size/test_size must be provided")
        if self.validation_end is not None and self.validation_end <= self.train_end:
            raise ValueError("validation_end must be after train_end")
        if self.test_end is not None:
            previous = (
                self.validation_end
                if self.validation_end is not None
                else self.train_end
            )
            if self.test_end <= previous:
                raise ValueError("test_end must be after preceding boundaries")

        membership = _membership(index)
        membership.loc[index <= self.train_end] = "train"
        next_start = index > self.train_end
        partitions = [_TRAIN]
        if self.validation_end is not None:
            membership.loc[next_start & (index <= self.validation_end)] = "validation"
            next_start &= index > self.validation_end
            partitions.append(_VALIDATION)
        test_mask = next_start
        if self.test_end is not None:
            test_mask &= index <= self.test_end
        membership.loc[test_mask] = "test"
        partitions.extend([_TEST, _EXCLUDED])
        return Split(
            membership,
            partitions,
            name=self.name,
            metadata={
                "method": "temporal",
                "train_end": self.train_end,
                "validation_end": self.validation_end,
                "test_end": self.test_end,
            },
        )

    def _split_by_size(self, index: pd.Index) -> Split:
        sizes = {
            "train": self.train_size,
            "test": self.test_size,
        }
        if self.validation_size is not None:
            sizes["validation"] = self.validation_size
        if self.train_size is None and self.test_size is None:
            raise ValueError("train_size or test_size must be provided")

        provided = [size for size in sizes.values() if size is not None]
        if any(isinstance(size, bool) or not isinstance(size, Real) for size in provided):
            raise ValueError("sizes must be positive integers or proportions")
        integer_sizes = all(isinstance(size, Integral) for size in provided)
        if not integer_sizes and any(isinstance(size, Integral) for size in provided):
            raise ValueError("integer row counts and float proportions cannot be mixed")

        total = len(index) if integer_sizes else 1.0
        if integer_sizes:
            if any(size <= 0 for size in provided):
                raise ValueError("integer sizes must be positive")
        elif any(size <= 0 or size >= 1 for size in provided):
            raise ValueError("float sizes must be between 0 and 1")

        missing = [name for name, size in sizes.items() if size is None]
        explicit_total = sum(provided)
        if len(missing) == 1:
            remainder = total - explicit_total
            if remainder <= 0:
                raise ValueError("sizes must leave rows for every partition")
            sizes[missing[0]] = remainder
        elif integer_sizes:
            if explicit_total != total:
                raise ValueError("integer sizes must sum to the dataset length")
        elif not isclose(explicit_total, total):
            raise ValueError("float sizes must sum to 1")

        ordered_names = ["train"]
        if self.validation_size is not None:
            ordered_names.append("validation")
        ordered_names.append("test")
        counts = {}
        consumed = 0
        cumulative = 0.0
        for position, partition in enumerate(ordered_names):
            if position == len(ordered_names) - 1:
                count = len(index) - consumed
            elif integer_sizes:
                count = int(sizes[partition])
            else:
                cumulative += float(sizes[partition])
                count = int(np.floor(cumulative * len(index))) - consumed
            if count <= 0:
                raise ValueError("dataset is too small for the requested sizes")
            counts[partition] = count
            consumed += count

        membership = _membership(index)
        start = 0
        partitions = [_TRAIN]
        for partition in ordered_names:
            stop = start + counts[partition]
            membership.iloc[start:stop] = partition
            start = stop
            if partition == "validation":
                partitions.append(_VALIDATION)
        partitions.extend([_TEST, _EXCLUDED])
        train_end = index[counts["train"] - 1]
        validation_end = (
            index[counts["train"] + counts["validation"] - 1]
            if "validation" in counts
            else None
        )
        return Split(
            membership,
            partitions,
            name=self.name,
            metadata={
                "method": "temporal",
                "train_end": train_end,
                "validation_end": validation_end,
                "test_end": index[-1],
                "train_size": self.train_size,
                "validation_size": self.validation_size,
                "test_size": self.test_size,
            },
        )

    def apply(self, dataset: Dataset) -> Dataset:
        """Return ``dataset`` with this split attached as the default scheme."""
        return dataset.with_split(self.split(dataset))


@dataclass(frozen=True)
class TimeSeriesSplit:
    """Wrap sklearn's expanding or rolling time-series cross-validator.

    ``max_train_size`` selects a rolling window; leaving it unset produces
    expanding training windows. ``gap`` and ``test_size`` retain sklearn's row
    semantics. Rows not selected in a fold receive the ``excluded`` role.
    """

    n_splits: int = 5
    max_train_size: int | None = None
    test_size: int | None = None
    gap: int = 0
    name: str = "walk_forward"

    def split(self, dataset: Dataset) -> SplitScheme:
        """Return sklearn-generated folds as a QRT split scheme."""
        index = _ordered_index(dataset)
        splitter = SklearnTimeSeriesSplit(
            n_splits=self.n_splits,
            max_train_size=self.max_train_size,
            test_size=self.test_size,
            gap=self.gap,
        )
        splits = []
        for number, (train, test) in enumerate(splitter.split(dataset.X), start=1):
            membership = _membership(index)
            membership.iloc[train] = "train"
            membership.iloc[test] = "test"
            splits.append(
                Split(
                    membership,
                    [_TRAIN, _TEST, _EXCLUDED],
                    name=f"fold_{number}",
                    metadata={
                        "train_start": index[train[0]],
                        "train_end": index[train[-1]],
                        "test_start": index[test[0]],
                        "test_end": index[test[-1]],
                    },
                )
            )
        return SplitScheme(
            splits,
            name=self.name,
            metadata={
                "method": "rolling" if self.max_train_size is not None else "expanding",
                "backend": "sklearn.model_selection.TimeSeriesSplit",
                "n_splits": self.n_splits,
                "max_train_size": self.max_train_size,
                "test_size": self.test_size,
                "gap": self.gap,
            },
        )

    def apply(self, dataset: Dataset) -> Dataset:
        """Return ``dataset`` with the generated scheme attached."""
        return dataset.with_split(self.split(dataset))


@dataclass(frozen=True)
class PurgedTimeSeriesSplit(TimeSeriesSplit):
    """Walk-forward folds purged by label horizons and optional embargo.

    Args:
        label_end: Metadata column containing each row's inclusive label end.
        embargo: Additional separation before each test partition, expressed as
            a row count or pandas-compatible timedelta string.
    """

    label_end: str = "label_end_time"
    embargo: int | str | pd.Timedelta = 0
    name: str = "purged_walk_forward"

    def split(self, dataset: Dataset) -> SplitScheme:
        """Return sklearn folds after removing overlapping training labels."""
        if dataset.metadata is None or self.label_end not in dataset.metadata:
            raise ValueError(f"dataset metadata must contain {self.label_end!r}")
        label_end = pd.to_datetime(dataset.metadata[self.label_end])
        if label_end.isna().any():
            raise ValueError("label end times must not contain missing values")

        base = super().split(dataset)
        splits = []
        for base_split in base.splits:
            membership = base_split.membership.copy()
            test_index = membership.index[membership.eq("test")]
            test_start = test_index[0]
            purge = membership.eq("train") & label_end.ge(test_start)
            membership.loc[purge] = "excluded"

            if isinstance(self.embargo, int):
                if self.embargo < 0:
                    raise ValueError("embargo must be non-negative")
                train_positions = np.flatnonzero(membership.eq("train").to_numpy())
                if self.embargo:
                    membership.iloc[train_positions[-self.embargo :]] = "excluded"
            else:
                delta = pd.Timedelta(self.embargo)
                if delta < pd.Timedelta(0):
                    raise ValueError("embargo must be non-negative")
                membership.loc[
                    membership.eq("train") & (membership.index > test_start - delta)
                ] = "excluded"

            metadata = dict(base_split.metadata)
            metadata.update(
                {
                    "purged_rows": int(purge.sum()),
                    "embargo": self.embargo,
                    "label_end": self.label_end,
                }
            )
            splits.append(
                Split(
                    membership,
                    base_split.partitions,
                    name=base_split.name,
                    metadata=metadata,
                )
            )
        scheme_metadata = dict(base.metadata)
        scheme_metadata.update({"method": "purged_walk_forward", "embargo": self.embargo})
        return SplitScheme(splits, name=self.name, metadata=scheme_metadata)


def split_diagnostics(dataset: Dataset, scheme: str, fold: int | str = 0) -> pd.DataFrame:
    """Summarize partition roles, sizes, proportions, and index boundaries."""
    if scheme not in dataset.splits:
        raise KeyError(f"unknown split scheme {scheme!r}")
    split = dataset.splits[scheme].split(fold)
    rows = []
    for partition in split.partitions:
        view = dataset.partition(partition.name, scheme=scheme, fold=fold)
        rows.append(
            {
                "partition": partition.name,
                "role": partition.role,
                "rows": len(view),
                "proportion": len(view) / len(dataset),
                "start": view.index.min() if len(view) else pd.NaT,
                "end": view.index.max() if len(view) else pd.NaT,
            }
        )
    return pd.DataFrame(rows).set_index("partition")


def audit_splits(
    dataset: Dataset,
    scheme: str,
    *,
    label_end: str = "label_end_time",
) -> pd.DataFrame:
    """Audit all folds for ordering and label-horizon leakage.

    A fold passes when every fit row precedes every evaluate/holdout row and,
    when label-end metadata exists, each fit label ends before evaluation starts.
    """
    if scheme not in dataset.splits:
        raise KeyError(f"unknown split scheme {scheme!r}")
    label_ends = None
    if dataset.metadata is not None and label_end in dataset.metadata:
        label_ends = pd.to_datetime(dataset.metadata[label_end])

    rows = []
    for split in dataset.splits[scheme].splits:
        fit_names = split.fit_partitions
        evaluation_names = tuple(
            partition.name
            for partition in split.partitions
            if partition.role in {"evaluate", "holdout"}
        )
        fit_mask = split.membership.isin(fit_names)
        evaluation_mask = split.membership.isin(evaluation_names)
        fit_index = dataset.index[fit_mask.to_numpy()]
        evaluation_index = dataset.index[evaluation_mask.to_numpy()]
        ordered = bool(
            len(fit_index)
            and len(evaluation_index)
            and fit_index.max() < evaluation_index.min()
        )
        horizons_clear = True
        if label_ends is not None and len(evaluation_index):
            horizons_clear = bool(
                label_ends.loc[fit_mask].lt(evaluation_index.min()).all()
            )
        rows.append(
            {
                "fold": split.name,
                "fit_rows": int(fit_mask.sum()),
                "evaluation_rows": int(evaluation_mask.sum()),
                "temporally_ordered": ordered,
                "label_horizons_clear": horizons_clear,
                "passed": ordered and horizons_clear,
            }
        )
    return pd.DataFrame(rows).set_index("fold")