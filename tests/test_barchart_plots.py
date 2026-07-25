import pandas as pd
import pytest
from plotly.graph_objects import Figure

import qrt as q


def test_barchart_sorts_values_and_colors_by_sign():
    values = pd.Series({"carry": 0.18, "value": -0.07, "momentum": 0.31})

    figure = q.plot.barchart(values, sorted=True, title="Strategy returns")

    assert isinstance(figure, Figure)
    assert list(figure.data[0].x) == ["momentum", "carry", "value"]
    assert list(figure.data[0].y) == [0.31, 0.18, -0.07]
    assert list(figure.data[0].marker.color) == ["#22C55E", "#22C55E", "#EF4444"]
    assert figure.layout.xaxis.tickangle == -90
    assert figure.layout.title.text == "Strategy returns"


def test_barchart_selects_and_aggregates_dataframe_columns():
    returns = pd.DataFrame(
        {
            "AAPL_return": [0.03, -0.01],
            "MSFT_return": [0.02, 0.04],
            "volume": [100, 120],
        }
    )

    figure = q.plot.barchart(returns, columns="*_return", aggregate="sum")

    assert list(figure.data[0].x) == ["AAPL_return", "MSFT_return"]
    assert list(figure.data[0].y) == pytest.approx([0.02, 0.06])


def test_barchart_accepts_custom_color_schemes():
    values = pd.Series({"carry": 0.18, "value": -0.07, "momentum": 0.31})

    mapped = q.plot.barchart(
        values,
        color_scheme={"carry": "#112233", "value": "#445566", "momentum": "#778899"},
    )
    cycled = q.plot.barchart(values, color_scheme=["#AABBCC", "#DDEEFF"])

    assert list(mapped.data[0].marker.color) == ["#112233", "#445566", "#778899"]
    assert list(cycled.data[0].marker.color) == ["#AABBCC", "#DDEEFF", "#AABBCC"]


def test_barchart_requires_aggregation_for_multiple_rows():
    with pytest.raises(ValueError, match="aggregate"):
        q.plot.barchart(pd.DataFrame({"A": [1.0, 2.0], "B": [3.0, 4.0]}))