"""Dataset-aware fitted transformation pipelines."""

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline as SklearnPipeline

from qrt.dataset import Dataset


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
        dataset: Dataset,
        *,
        scheme: str = "default",
        fold: int | str = 0,
    ) -> "Pipeline":
        """Fit sklearn transformers using only role-``fit`` partitions."""
        if not isinstance(dataset, Dataset):
            raise TypeError("dataset must be a qrt.dataset.Dataset")
        if scheme not in dataset.splits:
            raise KeyError(f"unknown split scheme {scheme!r}")
        split = dataset.splits[scheme].split(fold)
        if not split.fit_partitions:
            raise ValueError("split must define at least one fit partition")
        mask = split.membership.isin(split.fit_partitions)
        fit_index = dataset.index[mask.to_numpy()]
        if fit_index.empty:
            raise ValueError("fit partitions must contain at least one row")
        y = None if dataset.y is None else dataset.y.loc[fit_index]
        self.estimator.fit(dataset.X.loc[fit_index], y)
        self.fit_provenance_ = {
            "scheme": scheme,
            "fold": split.name,
            "partitions": split.fit_partitions,
            "rows": len(fit_index),
            "start": fit_index.min(),
            "end": fit_index.max(),
        }
        return self

    def transform(self, dataset: Dataset) -> Dataset:
        """Transform every row and preserve all non-feature components."""
        if self.fit_provenance_ is None:
            raise RuntimeError("pipeline must be fitted before transform")
        transformed = self.estimator.transform(dataset.X)
        if isinstance(transformed, pd.DataFrame):
            X = transformed.copy()
            X.index = dataset.index
        else:
            values = np.asarray(transformed)
            if values.ndim == 1:
                values = values.reshape(-1, 1)
            try:
                columns = self.estimator.get_feature_names_out()
            except (AttributeError, ValueError):
                columns = [f"feature_{position}" for position in range(values.shape[1])]
            X = pd.DataFrame(values, index=dataset.index, columns=columns)
        return Dataset(
            X,
            dataset.y,
            dataset.sample_weight,
            dataset.metadata,
            splits=dataset.splits,
        )

    def fit_transform(
        self,
        dataset: Dataset,
        *,
        scheme: str = "default",
        fold: int | str = 0,
    ) -> Dataset:
        """Fit on allowed rows, then transform the complete dataset."""
        return self.fit(dataset, scheme=scheme, fold=fold).transform(dataset)