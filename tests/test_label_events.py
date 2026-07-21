import numpy as np
import pandas as pd
import pytest

import qrt as q


def test_cusum_filter_detects_bidirectional_log_return_events():
    index = pd.date_range("2026-01-01", periods=6, name="datetime")
    prices = pd.Series([100, 101, 102, 100, 98, 99], index=index, dtype=float)
    original = prices.copy(deep=True)

    result = q.label.cusum_filter(prices, threshold=0.015)

    expected = index[[2, 3, 4]]
    pd.testing.assert_index_equal(result, expected)
    pd.testing.assert_series_equal(prices, original)


def test_cusum_filter_accepts_aligned_time_varying_thresholds():
    index = pd.date_range("2026-01-01", periods=5)
    prices = pd.Series([100, 102, 104, 101, 98], index=index, dtype=float)
    thresholds = pd.Series([np.nan, np.nan, 0.015, 0.02, 0.02], index=index)

    result = q.label.cusum_filter(prices, thresholds)

    pd.testing.assert_index_equal(result, index[[2, 3, 4]])


def test_cusum_filter_validates_order_alignment_and_parameters():
    index = pd.date_range("2026-01-01", periods=3)
    prices = pd.Series([100, 101, 102], index=index, dtype=float)

    with pytest.raises(ValueError, match="threshold must be positive"):
        q.label.cusum_filter(prices, 0)
    with pytest.raises(ValueError, match="threshold index must match"):
        q.label.cusum_filter(
            prices,
            pd.Series([0.01, 0.01, 0.01], index=index.shift(1)),
        )
    with pytest.raises(ValueError, match="sorted in increasing order"):
        q.label.cusum_filter(prices.iloc[::-1], 0.01)