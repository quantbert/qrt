"""Dataset-aware fitted transformation pipelines."""

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline as SklearnPipeline

from qrt.dataset import Dataset, Fold, Split

DatasetLike = Dataset | Fold


class Pipeline:
    """Wrap sklearn's pipeline with QRT split-aware fitting.

    Args:
        steps: Sklearn-style ``(name, transformer)`` pairs.

    Learned state is fitted only from partitions whose role is ``"fit"``.
    The fitted sklearn pipeline then transforms the complete aligned feature
    frame, retaining targets, weights, metadata, and split schemes.
    """

    def __init__(self, steps: Sequence[tuple[str, Any]]) -> None:
        self.estimator = SklearnPipeline(list(steps))
        self.fit_provenance_: dict[str, Any] | None = None

    def fit(
        self,
        dataset: DatasetLike,
        *,
        scheme: str | None = None,
        fold: int | str | None = None,
    ) -> "Pipeline":
        """Fit sklearn transformers using only role-``fit`` partitions."""
        parent, scheme_name, split = self._fit_context(dataset, scheme, fold)
        if not split.fit_partitions:
            raise ValueError("split must define at least one fit partition")
        mask = split.membership.isin(split.fit_partitions)
        fit_index = parent.index[mask.to_numpy()]
        if fit_index.empty:
            raise ValueError("fit partitions must contain at least one row")
        y = None if parent.y is None else parent.y.loc[fit_index]
        self.estimator.fit(parent.X.loc[fit_index], y)
        self.fit_provenance_ = {
            "scheme": scheme_name,
            "fold": split.name,
            "partitions": split.fit_partitions,
            "rows": len(fit_index),
            "start": fit_index.min(),
            "end": fit_index.max(),
        }
        return self

    def transform(self, dataset: DatasetLike) -> DatasetLike:
        """Transform every row and preserve all non-feature components."""
        if self.fit_provenance_ is None:
            raise RuntimeError("pipeline must be fitted before transform")
        if not isinstance(dataset, (Dataset, Fold)):
            raise TypeError("dataset must be a qrt.dataset.Dataset or Fold")
        parent = dataset.dataset if isinstance(dataset, Fold) else dataset
        transformed = self.estimator.transform(parent.X)
        if isinstance(transformed, pd.DataFrame):
            X = transformed.copy()
            X.index = parent.index
        else:
            values = np.asarray(transformed)
            if values.ndim == 1:
                values = values.reshape(-1, 1)
            try:
                columns = self.estimator.get_feature_names_out()
            except (AttributeError, ValueError):
                columns = [f"feature_{position}" for position in range(values.shape[1])]
            X = pd.DataFrame(values, index=parent.index, columns=columns)
        result = Dataset(
            X,
            parent.y,
            parent.sample_weight,
            parent.metadata,
            splits=parent.splits,
        )
        if isinstance(dataset, Fold):
            return result.fold(dataset.scheme.name, dataset.name)
        return result

    def fit_transform(
        self,
        dataset: DatasetLike,
        *,
        scheme: str | None = None,
        fold: int | str | None = None,
    ) -> DatasetLike:
        """Fit on allowed rows, then transform the complete dataset."""
        return self.fit(dataset, scheme=scheme, fold=fold).transform(dataset)

    @staticmethod
    def _fit_context(
        dataset: DatasetLike,
        scheme: str | None,
        fold: int | str | None,
    ) -> tuple[Dataset, str, Split]:
        if isinstance(dataset, Fold):
            if scheme is not None or fold is not None:
                raise ValueError("scheme and fold must be omitted for a bound Fold")
            return dataset.dataset, dataset.scheme.name, dataset.split
        if not isinstance(dataset, Dataset):
            raise TypeError("dataset must be a qrt.dataset.Dataset or Fold")
        scheme_name = "default" if scheme is None else scheme
        fold_name = 0 if fold is None else fold
        if scheme_name not in dataset.splits:
            raise KeyError(f"unknown split scheme {scheme_name!r}")
        return dataset, scheme_name, dataset.splits[scheme_name].split(fold_name)