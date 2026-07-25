import numpy as np
import pandas as pd
import pytest

import qrt as q


def test_random_walk_generates_reproducible_dated_price_paths():
    names = ["strategy_1", "strategy_2", "strategy_3"]
    first = q.stats.random_walk(
        periods=20,
        paths=3,
        drift=[-0.10, 0.05, 0.20],
        volatility=[0.10, 0.20, 0.30],
        start=50.0,
        start_date="2025-01-02",
        names=names,
        seed=7,
    )
    second = q.stats.random_walk(
        periods=20,
        paths=3,
        drift=[-0.10, 0.05, 0.20],
        volatility=[0.10, 0.20, 0.30],
        start=50.0,
        start_date="2025-01-02",
        names=names,
        seed=7,
    )

    pd.testing.assert_frame_equal(first, second)
    assert first.shape == (20, 3)
    assert first.columns.tolist() == names
    assert isinstance(first.index, pd.DatetimeIndex)
    assert first.index.name == "date"
    assert first.iloc[0].tolist() == [50.0, 50.0, 50.0]
    assert (first > 0).all().all()


def test_random_walk_uses_range_index_and_scalar_parameters_by_default():
    prices = q.stats.random_walk(periods=5, paths=2, seed=3)

    assert prices.shape == (5, 2)
    assert prices.columns.tolist() == ["path_1", "path_2"]
    assert prices.index.equals(pd.RangeIndex(5, name="period"))
    assert np.isfinite(prices.to_numpy()).all()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"periods": 0}, "periods"),
        ({"paths": 0}, "paths"),
        ({"start": 0}, "start"),
        ({"start": "invalid"}, "start"),
        ({"periods_per_year": 0}, "periods_per_year"),
        ({"paths": 2, "drift": [0.1]}, "drift"),
        ({"paths": 2, "volatility": [0.1]}, "volatility"),
        ({"volatility": -0.1}, "volatility"),
        ({"paths": 2, "names": ["only_one"]}, "names"),
        ({"paths": 2, "names": ["same", "same"]}, "unique"),
    ],
)
def test_random_walk_validates_inputs(kwargs, message):
    with pytest.raises((TypeError, ValueError), match=message):
        q.stats.random_walk(**kwargs)