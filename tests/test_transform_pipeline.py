import pandas as pd
import pytest
from sklearn.preprocessing import StandardScaler

import qrt as q


def test_pipeline_fits_only_fit_partitions_and_transforms_all_rows():
    index = pd.date_range("2024-01-01", periods=6)
    dataset = q.dataset.build(
        features=pd.DataFrame({"value": [0.0, 2.0, 4.0, 100.0, 200.0, 300.0]}, index=index),
        labels=pd.Series([0, 0, 1, 1, 1, 0], index=index),
    )
    dataset = q.dataset.TemporalSplit(train_end=index[2]).apply(dataset)
    pipeline = q.transform.Pipeline([("scale", StandardScaler())])

    transformed = pipeline.fit_transform(dataset)

    assert transformed.train.X["value"].mean() == pytest.approx(0.0)
    assert transformed.train.X["value"].std(ddof=0) == pytest.approx(1.0)
    assert transformed.test.X.iloc[0, 0] > 50
    pd.testing.assert_series_equal(transformed.y, dataset.y)
    assert transformed.splits.keys() == dataset.splits.keys()
    assert pipeline.fit_provenance_["rows"] == 3
    assert pipeline.fit_provenance_["partitions"] == ("train",)


def test_pipeline_requires_split_and_fit_role():
    dataset = q.dataset.Dataset(pd.DataFrame({"x": [1.0, 2.0]}))
    pipeline = q.transform.Pipeline([("scale", StandardScaler())])

    with pytest.raises(KeyError, match="unknown split scheme"):
        pipeline.fit(dataset)
    with pytest.raises(RuntimeError, match="must be fitted"):
        pipeline.transform(dataset)