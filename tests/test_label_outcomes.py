import pandas as pd
import pytest

import qrt as q


def test_prune_labels_removes_rare_class_and_reports_decision():
    index = pd.date_range("2026-01-01", periods=11, name="event_time")
    labels = pd.Series([0] * 8 + [1] * 2 + [-1], index=index, name="label")

    retained, report = q.label.prune_labels(labels, min_fraction=0.15)

    pd.testing.assert_series_equal(retained, labels.iloc[:10])
    assert report.loc[-1, "initial_count"] == 1
    assert report.loc[-1, "final_count"] == 0
    assert report.loc[-1, "dropped"]
    assert report.loc[-1, "drop_step"] == 1
    assert not report.loc[0, "dropped"]


def test_prune_labels_preserves_requested_minimum_class_count():
    index = pd.RangeIndex(10, name="event_time")
    labels = pd.Series([0] * 9 + [1], index=index)

    retained, report = q.label.prune_labels(
        labels,
        min_fraction=0.25,
        min_classes=2,
    )

    pd.testing.assert_series_equal(retained, labels)
    assert not report["dropped"].any()


def test_prune_labels_breaks_frequency_ties_by_first_observation():
    index = pd.RangeIndex(12, name="event_time")
    labels = pd.Series([0] * 8 + [2, 1, 2, 1], index=index)

    retained, report = q.label.prune_labels(
        labels,
        min_fraction=0.2,
        min_classes=2,
    )

    assert 2 not in retained.to_numpy()
    assert 1 in retained.to_numpy()
    assert report.loc[2, "drop_step"] == 1


@pytest.mark.parametrize("min_fraction", [0, -0.1, 1.1])
def test_prune_labels_rejects_invalid_minimum_fraction(min_fraction):
    labels = pd.Series([0, 1], index=pd.RangeIndex(2))

    with pytest.raises(ValueError, match="min_fraction"):
        q.label.prune_labels(labels, min_fraction=min_fraction)


def test_prune_labels_rejects_missing_targets():
    labels = pd.Series([0, pd.NA, 1], index=pd.RangeIndex(3), dtype="Int8")

    with pytest.raises(ValueError, match="must not contain missing"):
        q.label.prune_labels(labels)