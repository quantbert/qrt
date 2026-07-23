import pandas as pd
import pytest

import qrt as q


def test_pipeline_fits_only_fit_partitions_and_transforms_all_rows():
    index = pd.date_range("2024-01-01", periods=6)
    dataset = q.dataset.Dataset(
        X=pd.DataFrame({"value": [0.0, 2.0, 4.0, 100.0, 200.0, 300.0]}, index=index),
        y=pd.Series([0, 0, 1, 1, 1, 0], index=index),
    )
    dataset = q.dataset.TemporalSplit(train_end=index[2]).apply(dataset)
    pipeline = q.transform.Pipeline(
        [("scale", q.transform.scale.StandardScaler())]
    )

    transformed = pipeline.fit_transform(dataset)

    assert transformed.train.X["value"].mean() == pytest.approx(0.0)
    assert transformed.train.X["value"].std(ddof=0) == pytest.approx(1.0)
    assert transformed.test.X.iloc[0, 0] > 50
    pd.testing.assert_series_equal(transformed.y, dataset.y)
    assert transformed.splits.keys() == dataset.splits.keys()
    assert pipeline.fit_provenance_["rows"] == 3
    assert pipeline.fit_provenance_["partitions"] == ("train",)


def test_pipeline_accepts_and_returns_a_bound_fold():
    index = pd.date_range("2024-01-01", periods=6)
    dataset = q.dataset.Dataset(
        pd.DataFrame({"value": [0.0, 2.0, 100.0, 200.0, 300.0, 400.0]}, index=index)
    ).split(q.dataset.TimeSeriesSplit(n_splits=2, test_size=2, name="cv"))
    fold = next(iter(dataset.splits["cv"]))
    pipeline = q.transform.Pipeline(
        [("scale", q.transform.scale.StandardScaler())]
    )

    transformed = pipeline.fit_transform(fold)

    assert isinstance(transformed, q.dataset.Fold)
    assert transformed.name == "fold_1"
    assert transformed.train.X["value"].mean() == pytest.approx(0.0)
    assert transformed.test.X.iloc[0, 0] > 50
    assert pipeline.fit_provenance_["scheme"] == "cv"
    assert pipeline.fit_provenance_["fold"] == "fold_1"


def test_pipeline_requires_split_and_fit_role():
    dataset = q.dataset.Dataset(pd.DataFrame({"x": [1.0, 2.0]}))
    pipeline = q.transform.Pipeline(
        [("scale", q.transform.scale.StandardScaler())]
    )

    with pytest.raises(KeyError, match="unknown split scheme"):
        pipeline.fit(dataset)
    with pytest.raises(RuntimeError, match="must be fitted"):
        pipeline.transform(dataset)


def test_pipeline_imputes_with_q_transform_public_api():
    index = pd.date_range("2024-01-01", periods=4)
    dataset = q.dataset.Dataset(
        pd.DataFrame({"value": [1.0, None, 3.0, None]}, index=index)
    ).split(q.dataset.TemporalSplit(train_end=index[2]))
    pipeline = q.transform.Pipeline(
        [("impute", q.transform.impute.SimpleImputer(strategy="median"))]
    )

    transformed = pipeline.fit_transform(dataset)

    assert transformed.X["value"].tolist() == [1.0, 2.0, 3.0, 2.0]