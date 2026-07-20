import pandas as pd

import qrt as q


class MemorySink:
    def __init__(self):
        self.table = None
        self.data = None

    def write(self, data: pd.DataFrame, *, table: str) -> None:
        self.table = table
        self.data = data.copy()


def test_feature_set_computes_per_entity_and_materializes():
    data = pd.DataFrame(
        {
            "symbol": ["A", "A", "B", "B"],
            "datetime": pd.to_datetime(
                ["2026-01-01", "2026-01-02", "2026-01-01", "2026-01-02"]
            ),
            "close": [1.0, 3.0, 10.0, 14.0],
        }
    )
    feature = q.feature.Feature(
        name="sma_2",
        function=lambda series, window: series.rolling(window).mean(),
        inputs={"series": "close"},
        params={"window": 2},
        lookback=2,
        available_at="bar_close",
    )
    features = q.feature.FeatureSet([feature], name="prices")
    sink = MemorySink()

    result = q.feature.materialize(features, data, sink, table="features")

    expected = pd.Series([float("nan"), 2.0, float("nan"), 12.0], name="sma_2")
    pd.testing.assert_series_equal(result["sma_2"], expected)
    assert result.columns.tolist() == ["symbol", "datetime", "sma_2"]
    assert sink.table == "features"
    pd.testing.assert_frame_equal(sink.data, result)


def test_feature_set_rejects_unsorted_entity_history():
    data = pd.DataFrame(
        {
            "symbol": ["A", "A"],
            "datetime": pd.to_datetime(["2026-01-02", "2026-01-01"]),
            "close": [2.0, 1.0],
        }
    )
    feature = q.feature.Feature(
        name="rank",
        function=lambda series: series.rank(),
        inputs={"series": "close"},
    )

    try:
        q.feature.compute(q.feature.FeatureSet([feature]), data)
    except ValueError as exc:
        assert "ordered by 'datetime'" in str(exc)
    else:
        raise AssertionError("unsorted entity history should raise ValueError")