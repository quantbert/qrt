import numpy as np
import pandas as pd
import pytest

import qrt as q


@pytest.fixture
def overlapping_events():
    observations = pd.date_range("2026-01-01", periods=5, name="datetime")
    end_times = pd.Series(
        observations[[2, 3]],
        index=observations[[0, 1]].rename("event_time"),
        name="touch_time",
    )
    return observations, end_times


def test_concurrency_counts_inclusive_overlapping_intervals(overlapping_events):
    observations, end_times = overlapping_events

    result = q.label.concurrency(observations, end_times)

    expected = pd.Series([1, 2, 2, 1, 0], index=observations, name="concurrency")
    pd.testing.assert_series_equal(result, expected)


def test_indicator_matrix_is_sparse_and_reproduces_concurrency(overlapping_events):
    observations, end_times = overlapping_events

    result = q.label.indicator_matrix(observations, end_times)

    expected = pd.DataFrame(
        [[1, 0], [1, 1], [1, 1], [0, 1], [0, 0]],
        index=observations,
        columns=end_times.index,
        dtype=np.int8,
    )
    pd.testing.assert_frame_equal(result.sparse.to_dense(), expected)
    assert all(isinstance(dtype, pd.SparseDtype) for dtype in result.dtypes)
    pd.testing.assert_series_equal(
        result.sum(axis=1).astype("int64").rename("concurrency"),
        q.label.concurrency(observations, end_times),
    )


def test_purging_metadata_tracks_running_end_and_embargo(overlapping_events):
    observations, end_times = overlapping_events

    result = q.label.purging_metadata(observations, end_times, embargo=1)

    assert result["end_time"].tolist() == end_times.tolist()
    assert result["max_end_time"].tolist() == observations[[2, 3]].tolist()
    assert result["overlaps_previous"].tolist() == [False, True]
    assert result["next_safe_position"].tolist() == [4, pd.NA]
    assert result["next_safe_time"].iloc[0] == observations[4]
    assert pd.isna(result["next_safe_time"].iloc[1])
    assert result["next_safe_time"].dtype == observations.dtype


def test_purging_metadata_uses_running_maximum_for_nested_events():
    observations = pd.RangeIndex(6, name="observation")
    end_times = pd.Series(
        [4, 2],
        index=pd.Index([0, 1], name="event_time"),
    )

    result = q.label.purging_metadata(observations, end_times)

    assert result["max_end_position"].tolist() == [4, 4]
    assert result["max_end_time"].tolist() == [4, 4]
    assert result["next_safe_position"].tolist() == [5, 5]


def test_purging_metadata_uses_nullable_integer_safe_times_when_exhausted():
    observations = pd.RangeIndex(3, name="observation")
    end_times = pd.Series([2], index=pd.Index([0], name="event_time"))

    result = q.label.purging_metadata(observations, end_times)

    assert result["next_safe_time"].dtype == "Int64"
    assert result["next_safe_time"].tolist() == [pd.NA]


def test_purging_metadata_rejects_invalid_embargo(overlapping_events):
    observations, end_times = overlapping_events

    with pytest.raises(ValueError, match="non-negative integer"):
        q.label.purging_metadata(observations, end_times, embargo=-1)


def test_sequential_bootstrap_is_reproducible_and_preserves_event_labels(
    overlapping_events,
):
    observations, end_times = overlapping_events

    first = q.label.sequential_bootstrap(
        observations,
        end_times,
        size=8,
        random_state=42,
    )
    second = q.label.sequential_bootstrap(
        observations,
        end_times,
        size=8,
        random_state=42,
    )

    pd.testing.assert_index_equal(first, second)
    assert first.name == "event_time"
    assert len(first) == 8
    assert first.isin(end_times.index).all()
    assert first.has_duplicates


def test_sequential_bootstrap_defaults_to_event_count(overlapping_events):
    observations, end_times = overlapping_events

    result = q.label.sequential_bootstrap(
        observations,
        end_times,
        random_state=0,
    )

    assert len(result) == len(end_times)


def test_empty_interval_utilities_return_empty_labeled_results():
    observations = pd.RangeIndex(3, name="observation")
    end_times = pd.Series(
        index=pd.Index([], dtype="int64", name="event_time"),
        dtype="int64",
    )

    matrix = q.label.indicator_matrix(observations, end_times)
    sample = q.label.sequential_bootstrap(observations, end_times, random_state=0)

    assert matrix.shape == (3, 0)
    pd.testing.assert_index_equal(matrix.index, observations)
    pd.testing.assert_index_equal(sample, end_times.index)


def test_sequential_bootstrap_rejects_invalid_size(overlapping_events):
    observations, end_times = overlapping_events

    with pytest.raises(ValueError, match="non-negative integer"):
        q.label.sequential_bootstrap(observations, end_times, size=-1)


def test_average_uniqueness_is_mean_inverse_concurrency(overlapping_events):
    observations, end_times = overlapping_events

    result = q.label.average_uniqueness(observations, end_times)

    expected = pd.Series(
        [2 / 3, 2 / 3],
        index=end_times.index,
        name="average_uniqueness",
    )
    pd.testing.assert_series_equal(result, expected)


def test_sample_weights_attribute_returns_and_optionally_normalize(overlapping_events):
    observations, end_times = overlapping_events
    prices = pd.Series([100, 110, 121, 108.9, 108.9], index=observations)

    raw = q.label.sample_weights(prices, end_times, normalize=False)
    normalized = q.label.sample_weights(prices, end_times)

    expected_first = np.log(1.1)
    expected_second = abs(np.log(1.1) + np.log(0.9))
    assert raw.to_numpy() == pytest.approx([expected_first, expected_second])
    assert normalized.sum() == pytest.approx(2.0)
    assert (normalized >= 0).all()


def test_time_decay_uses_cumulative_importance_and_reaches_one():
    index = pd.date_range("2026-01-01", periods=3, name="event_time")
    importance = pd.Series([1.0, 1.0, 2.0], index=index)

    result = q.label.time_decay(importance, minimum_weight=0.2)

    expected = pd.Series([0.4, 0.6, 1.0], index=index, name="time_decay")
    pd.testing.assert_series_equal(result, expected)


def test_class_balance_weights_give_each_class_equal_total_weight():
    index = pd.date_range("2026-01-01", periods=6, name="event_time")
    labels = pd.Series([0, 0, 0, 0, 1, 1], index=index)

    result = q.label.class_balance_weights(labels)

    assert result.mean() == pytest.approx(1.0)
    assert result[labels.eq(0)].sum() == pytest.approx(3.0)
    assert result[labels.eq(1)].sum() == pytest.approx(3.0)


def test_combine_weights_multiplies_aligned_components_and_normalizes():
    index = pd.date_range("2026-01-01", periods=3, name="event_time")
    uniqueness = pd.Series([0.5, 1.0, 1.0], index=index)
    decay = pd.Series([0.2, 0.6, 1.0], index=index)

    raw = q.label.combine_weights(uniqueness, decay, normalize=False)
    normalized = q.label.combine_weights(uniqueness, decay)

    pd.testing.assert_series_equal(
        raw,
        pd.Series([0.1, 0.6, 1.0], index=index, name="sample_weight"),
    )
    assert normalized.mean() == pytest.approx(1.0)


def test_weight_components_reject_invalid_values_and_alignment():
    index = pd.date_range("2026-01-01", periods=2)

    with pytest.raises(ValueError, match="at least one positive"):
        q.label.time_decay(pd.Series([0.0, 0.0], index=index))
    with pytest.raises(ValueError, match="less than or equal to 1"):
        q.label.time_decay(pd.Series([1.0, 1.0], index=index), minimum_weight=1.1)
    with pytest.raises(ValueError, match="same index"):
        q.label.combine_weights(
            pd.Series([1.0, 1.0], index=index),
            pd.Series([1.0, 1.0], index=index.shift(1)),
        )
    with pytest.raises(ValueError, match="non-negative"):
        q.label.combine_weights(pd.Series([1.0, -1.0], index=index))
    with pytest.raises(ValueError, match="positive value"):
        q.label.combine_weights(pd.Series([0.0, 0.0], index=index))


def test_empty_class_weights_and_disabled_decay_are_well_defined():
    empty = pd.Series(index=pd.RangeIndex(0), dtype="Int8")
    index = pd.RangeIndex(2)

    pd.testing.assert_series_equal(
        q.label.class_balance_weights(empty),
        pd.Series(index=empty.index, dtype=float, name="class_balance_weight"),
    )
    pd.testing.assert_series_equal(
        q.label.time_decay(
            pd.Series([1.0, 1.0], index=index),
            minimum_weight=1.0,
        ),
        pd.Series([1.0, 1.0], index=index, name="time_decay"),
    )


def test_weighting_utilities_reject_invalid_intervals(overlapping_events):
    observations, end_times = overlapping_events
    missing = end_times.copy()
    missing.iloc[0] = pd.NaT
    reversed_interval = end_times.copy()
    reversed_interval.iloc[1] = observations[0]

    with pytest.raises(ValueError, match="must not contain missing"):
        q.label.concurrency(observations, missing)
    with pytest.raises(ValueError, match="at or after"):
        q.label.average_uniqueness(observations, reversed_interval)