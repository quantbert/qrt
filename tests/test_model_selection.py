import numpy as np
from sklearn.model_selection import TimeSeriesSplit

import qrt as q


def test_timeseries_split_matches_sklearn_position_arrays():
    X = np.arange(24).reshape(12, 2)

    result = list(
        q.model.selection.timeseries_split(
            X, n_splits=3, test_size=2, max_train_size=4, gap=1
        )
    )
    expected = list(
        TimeSeriesSplit(
            n_splits=3, test_size=2, max_train_size=4, gap=1
        ).split(X)
    )

    for actual, reference in zip(result, expected, strict=True):
        np.testing.assert_array_equal(actual[0], reference[0])
        np.testing.assert_array_equal(actual[1], reference[1])