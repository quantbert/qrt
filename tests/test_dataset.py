import warnings

import pandas as pd
import pytest
from sklearn.model_selection import TimeSeriesSplit as SklearnTimeSeriesSplit

import qrt as q


@pytest.fixture
def dataset():
    index = pd.date_range("2024-01-01", periods=5, name="event_time")
    return q.dataset.Dataset(
        X=pd.DataFrame(
            {"momentum": [0.1, 0.2, -0.1, 0.3, 0.0]}, index=index
        ),
        y=pd.Series([1, 1, 0, 1, 0], index=index, name="target"),
        sample_weight=pd.Series(
            [1.0, 0.8, 1.2, 1.0, 0.9], index=index, name="sample_weight"
        ),
        metadata=pd.DataFrame(
            {
                "symbol": ["A", "A", "A", "B", "B"],
                "label_end_time": index + pd.Timedelta(days=2),
            },
            index=index,
        ),
    )


def test_dataset_keeps_all_components_aligned_without_requiring_a_split(dataset):
    pd.testing.assert_index_equal(dataset.X.index, dataset.y.index)
    pd.testing.assert_index_equal(dataset.X.index, dataset.sample_weight.index)
    pd.testing.assert_index_equal(dataset.X.index, dataset.metadata.index)
    assert len(dataset) == 5
    assert not dataset.is_split
    assert dict(dataset.splits) == {}


def test_dataset_aligns_components_on_named_keys():
    datetimes = pd.to_datetime(["2024-01-01", "2024-01-02"])
    features = pd.DataFrame(
        {
            "symbol": ["A", "B"],
            "datetime": datetimes,
            "momentum": [0.1, 0.2],
        }
    )
    labels = pd.DataFrame(
        {
            "symbol": ["B", "A"],
            "datetime": datetimes[::-1],
            "target": [1, 0],
        }
    )
    keyed_index = pd.MultiIndex.from_arrays(
        [["B", "A"], datetimes[::-1]], names=["symbol", "datetime"]
    )
    sample_weights = pd.Series([2.0, 1.0], index=keyed_index, name="weight")
    metadata = pd.DataFrame(
        {
            "symbol": ["B", "A"],
            "datetime": datetimes[::-1],
            "sector": ["finance", "technology"],
        }
    )

    result = q.dataset.Dataset(
        X=features,
        y=labels,
        sample_weight=sample_weights,
        metadata=metadata,
        on=["symbol", "datetime"],
    )

    expected_index = pd.MultiIndex.from_frame(features[["symbol", "datetime"]])
    pd.testing.assert_index_equal(result.index, expected_index)
    pd.testing.assert_frame_equal(result.X, features.set_index(["symbol", "datetime"]))
    assert result.y["target"].tolist() == [0, 1]
    assert result.sample_weight.tolist() == [1.0, 2.0]
    assert result.metadata["sector"].tolist() == ["technology", "finance"]


def test_dataset_on_rejects_duplicate_or_mismatched_keys():
    duplicate_features = pd.DataFrame(
        {"symbol": ["A", "A"], "datetime": [1, 1], "value": [1.0, 2.0]}
    )
    with pytest.raises(ValueError, match="X keys must be unique"):
        q.dataset.Dataset(
            X=duplicate_features,
            on=["symbol", "datetime"],
        )

    features = pd.DataFrame(
        {"symbol": ["A", "B"], "datetime": [1, 2], "value": [1.0, 2.0]}
    )
    labels = pd.DataFrame(
        {"symbol": ["A", "C"], "datetime": [1, 3], "target": [0, 1]}
    )
    with pytest.raises(ValueError, match="y keys must exactly match"):
        q.dataset.Dataset(
            X=features,
            y=labels,
            on=["symbol", "datetime"],
        )


def test_dataset_rejects_components_with_different_or_duplicate_indexes():
    index = pd.RangeIndex(2)
    features = pd.DataFrame({"x": [1.0, 2.0]}, index=index)

    with pytest.raises(ValueError, match="exactly the same index"):
        q.dataset.Dataset(
            X=features,
            y=pd.Series([0, 1], index=pd.RangeIndex(1, 3)),
        )
    with pytest.raises(ValueError, match="must be unique"):
        q.dataset.Dataset(pd.DataFrame({"x": [1.0, 2.0]}, index=[0, 0]))


def test_with_split_returns_aligned_partition_views_without_mutating_source(dataset):
    membership = pd.Series(
        ["train", "train", "validation", "test", "test"],
        index=dataset.index,
        name="partition",
    )
    split = q.dataset.Split(
        membership,
        [
            q.dataset.Partition("train", role="fit"),
            q.dataset.Partition("validation", role="evaluate"),
            q.dataset.Partition("test", role="holdout"),
        ],
        metadata={"method": "temporal", "embargo": "2D"},
    )

    result = dataset.with_split(split)

    assert dict(dataset.splits) == {}
    assert result.is_split
    assert tuple(result.partitions) == ("train", "validation", "test")
    assert result["train"].index.equals(result.train.index)
    assert result.train.dataset is result
    assert result.train.split.fit_partitions == ("train",)
    assert result.train.index.tolist() == dataset.index[:2].tolist()
    pd.testing.assert_frame_equal(result.validation.X, dataset.X.iloc[[2]])
    pd.testing.assert_series_equal(result.test.y, dataset.y.iloc[3:])
    pd.testing.assert_series_equal(
        result.test.sample_weight, dataset.sample_weight.iloc[3:]
    )
    pd.testing.assert_frame_equal(result.test.metadata, dataset.metadata.iloc[3:])
    assert result.test.partition.role == "holdout"
    assert result.train.split.metadata["embargo"] == "2D"


def test_named_scheme_supports_arbitrary_partitions_and_folds(dataset):
    partitions = [
        q.dataset.Partition("estimation", role="fit"),
        q.dataset.Partition("calibration", role="fit"),
        q.dataset.Partition("live", role="holdout"),
    ]
    first = q.dataset.Split(
        pd.Series(
            ["estimation", "estimation", "calibration", "live", "live"],
            index=dataset.index,
        ),
        partitions,
        name="fold_1",
    )
    second = q.dataset.Split(
        pd.Series(
            ["estimation", "estimation", "estimation", "calibration", "live"],
            index=dataset.index,
        ),
        partitions,
        name="fold_2",
    )
    scheme = q.dataset.SplitScheme(
        [first, second], name="walk_forward", metadata={"method": "expanding"}
    )

    result = dataset.with_split(scheme)

    assert list(scheme) == [first, second]
    assert [fold.name for fold in result.splits["walk_forward"]] == [
        "fold_1",
        "fold_2",
    ]
    bound_fold = result.splits["walk_forward"]["fold_2"]
    assert isinstance(bound_fold, q.dataset.Fold)
    assert tuple(bound_fold.partitions) == ("estimation", "calibration", "live")
    assert bound_fold["calibration"].index.tolist() == [dataset.index[3]]
    assert result.splits["walk_forward"].metadata["method"] == "expanding"
    assert first.fit_partitions == ("estimation", "calibration")
    assert result.partition(
        "calibration", scheme="walk_forward", fold="fold_2"
    ).index.tolist() == [dataset.index[3]]


def test_split_rejects_missing_unknown_and_misaligned_membership(dataset):
    partitions = [q.dataset.Partition("train", role="fit")]

    with pytest.raises(ValueError, match="assign every row"):
        q.dataset.Split(pd.Series(["train", None]), partitions)
    with pytest.raises(ValueError, match="unknown partitions"):
        q.dataset.Split(pd.Series(["train", "test"]), partitions)

    split = q.dataset.Split(
        pd.Series("train", index=pd.RangeIndex(len(dataset))), partitions
    )
    with pytest.raises(ValueError, match="exactly the same index"):
        dataset.with_split(split)


def test_temporal_split_creates_conventional_views_and_excludes_later_rows():
    index = pd.date_range("2024-01-01", periods=8)
    dataset = q.dataset.Dataset(pd.DataFrame({"x": range(8)}, index=index))

    result = dataset.split(
        q.dataset.TemporalSplit(
            train_end=index[2], validation_end=index[4], test_end=index[6]
        )
    )

    assert result.train.index.tolist() == index[:3].tolist()
    assert result.validation.index.tolist() == index[3:5].tolist()
    assert result.test.index.tolist() == index[5:7].tolist()
    assert result.partition("excluded").index.tolist() == [index[7]]


def test_temporal_split_accepts_proportional_sizes_and_infers_remainder():
    index = pd.date_range("2024-01-01", periods=20)
    dataset = q.dataset.Dataset(pd.DataFrame({"x": range(20)}, index=index))

    result = dataset.split(
        q.dataset.TemporalSplit(
            train_size=0.70,
            validation_size=0.15,
            test_size=0.15,
        )
    )
    inferred = dataset.split(
        q.dataset.TemporalSplit(train_size=14, validation_size=3)
    )

    assert result.train.index.tolist() == index[:14].tolist()
    assert result.validation.index.tolist() == index[14:17].tolist()
    assert result.test.index.tolist() == index[17:].tolist()
    assert inferred.test.index.tolist() == index[17:].tolist()
    assert result.train.split.metadata["train_end"] == index[13]


def test_temporal_split_size_mode_rejects_ambiguous_or_invalid_sizes(dataset):
    with pytest.raises(ValueError, match="boundaries and sizes cannot be combined"):
        q.dataset.TemporalSplit(train_end=dataset.index[1], test_size=2).split(dataset)
    with pytest.raises(ValueError, match="float sizes must sum to 1"):
        q.dataset.TemporalSplit(train_size=0.7, test_size=0.2).split(dataset)
    with pytest.raises(ValueError, match="cannot be mixed"):
        q.dataset.TemporalSplit(train_size=3, test_size=0.4).split(dataset)


def test_time_series_split_matches_sklearn_and_supports_rolling_windows():
    index = pd.date_range("2024-01-01", periods=12)
    dataset = q.dataset.Dataset(pd.DataFrame({"x": range(12)}, index=index))
    splitter = q.dataset.TimeSeriesSplit(
        n_splits=3, test_size=2, gap=1, max_train_size=4
    )

    scheme = splitter.split(dataset)
    expected = list(
        SklearnTimeSeriesSplit(
            n_splits=3, test_size=2, gap=1, max_train_size=4
        ).split(dataset.X)
    )

    assert scheme.metadata["backend"].endswith("TimeSeriesSplit")
    assert scheme.metadata["method"] == "rolling"
    for split, (train, test) in zip(scheme.splits, expected, strict=True):
        assert split.membership.index[split.membership.eq("train")].tolist() == index[
            train
        ].tolist()
        assert split.membership.index[split.membership.eq("test")].tolist() == index[
            test
        ].tolist()


def test_purged_time_series_split_removes_overlapping_labels_and_embargo_rows():
    index = pd.date_range("2024-01-01", periods=12)
    dataset = q.dataset.Dataset(
        X=pd.DataFrame({"x": range(12)}, index=index),
        metadata=pd.DataFrame(
            {"label_end_time": index + pd.Timedelta(days=2)}, index=index
        ),
    )

    scheme = q.dataset.PurgedTimeSeriesSplit(
        n_splits=3, test_size=2, embargo=1
    ).split(dataset)
    first = scheme.split("fold_1")
    train_index = first.membership.index[first.membership.eq("train")]
    test_index = first.membership.index[first.membership.eq("test")]

    assert dataset.metadata.loc[train_index, "label_end_time"].lt(test_index.min()).all()
    assert first.metadata["purged_rows"] == 2
    assert train_index.max() == index[2]


def test_purged_time_series_split_accepts_timedelta_embargo():
    index = pd.date_range("2024-01-01", periods=12)
    dataset = q.dataset.Dataset(
        X=pd.DataFrame({"x": range(12)}, index=index),
        metadata=pd.DataFrame({"label_end_time": index}, index=index),
    )

    split = q.dataset.PurgedTimeSeriesSplit(
        n_splits=3, test_size=2, embargo="3D"
    ).split(dataset).split(0)
    train_index = split.membership.index[split.membership.eq("train")]
    test_index = split.membership.index[split.membership.eq("test")]

    assert train_index.max() <= test_index.min() - pd.Timedelta("3D")


def test_split_diagnostics_audit_and_serialization_round_trip(dataset, tmp_path):
    split_dataset = q.dataset.PurgedTimeSeriesSplit(
        n_splits=2, test_size=1
    ).apply(dataset)

    diagnostics = q.dataset.split_diagnostics(
        split_dataset, "purged_walk_forward", "fold_1"
    )
    audit = q.dataset.audit_splits(split_dataset, "purged_walk_forward")
    path = tmp_path / "dataset.joblib"
    split_dataset.save(path)
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        restored = q.dataset.Dataset.load(path)

    assert diagnostics["rows"].sum() == len(dataset)
    assert audit["passed"].all()
    pd.testing.assert_frame_equal(restored.X, split_dataset.X)
    pd.testing.assert_series_equal(
        restored.splits["purged_walk_forward"].split(0).membership,
        split_dataset.splits["purged_walk_forward"].split(0).membership,
    )