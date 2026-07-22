"""Compatibility helpers for array-based model selection.

Aligned financial datasets and split metadata are owned by :mod:`qrt.dataset`.
This module retains an array-index generator for callers that need sklearn's
native interface.

    q.model.selection.timeseries_split(X, n_splits=5, gap=5)

Examples:
    >>> for train_idx, test_idx in q.model.selection.timeseries_split(X, n_splits=5):
    ...     ...
"""


from sklearn.model_selection import TimeSeriesSplit


def timeseries_split(
    X,
    n_splits: int = 5,
    *,
    max_train_size: int | None = None,
    test_size: int | None = None,
    gap: int = 0,
):
    """Yield sklearn expanding or rolling train/test position arrays.

    Use :class:`qrt.dataset.TimeSeriesSplit` when aligned features, targets,
    metadata, named partitions, diagnostics, or purging are required.
    """
    return TimeSeriesSplit(
        n_splits=n_splits,
        max_train_size=max_train_size,
        test_size=test_size,
        gap=gap,
    ).split(X)
