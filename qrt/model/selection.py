"""Model selection: leakage-aware CV splitters for time-series data.

Naming mirrors scikit-learn's ``model_selection`` (e.g. ``TimeSeriesSplit``)
under ``q.model.selection``.

    q.model.selection.timeseries_split(X, n_splits=5, embargo="5D")

Examples:
    >>> for train_idx, test_idx in q.model.selection.timeseries_split(X, n_splits=5):
    ...     ...
"""


def timeseries_split(X, n_splits: int = 5, embargo=None):
    """Walk-forward (expanding-window) splits. Placeholder."""
    raise NotImplementedError
