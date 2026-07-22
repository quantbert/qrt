import pandas as pd
import pytest
from plotly.graph_objects import Figure

import qrt as q


@pytest.fixture
def label_plot_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    index = pd.date_range("2026-01-01", periods=7, name="datetime")
    prices = pd.DataFrame(
        {
            "open": [100, 101, 102, 101, 103, 101, 100],
            "high": [102, 103, 103, 104, 104, 102, 101],
            "low": [99, 100, 100, 100, 100, 99, 98],
            "close": [101, 102, 101, 103, 101, 100, 99],
        },
        index=index,
    )
    labels = pd.DataFrame(
        {
            "touch_time": index[[2, 5, 6]],
            "return": [0.02, 0.0, -0.03],
            "label": pd.array([1, 0, -1], dtype="Int8"),
        },
        index=index[[0, 3, 4]].rename("event_time"),
    )
    return prices, labels


def test_labels_plot_uses_directional_markers_and_outcome_spans(label_plot_data):
    prices, labels = label_plot_data

    figure = q.plot.labels(prices, labels, title="Event outcomes")

    assert isinstance(figure, Figure)
    assert [trace.name for trace in figure.data] == [
        "close",
        "Long",
        "Hold",
        "Short",
    ]
    assert [trace.marker.symbol for trace in figure.data[1:]] == [
        "triangle-up",
        "line-ew",
        "triangle-down",
    ]
    assert [trace.marker.color for trace in figure.data[1:]] == [
        "#16856B",
        "#F59E0B",
        "#D04A35",
    ]
    assert len(figure.layout.shapes) == 3
    assert [shape.fillcolor for shape in figure.layout.shapes] == [
        "#16856B",
        "#F59E0B",
        "#D04A35",
    ]
    assert figure.layout.title.text == "Event outcomes"


def test_labels_plot_accepts_series_and_can_disable_spans(label_plot_data):
    prices, labels = label_plot_data
    series = labels["label"].copy()
    series.iloc[1] = pd.NA

    figure = q.plot.labels(prices["close"], series, show_spans=False)

    assert [trace.name for trace in figure.data] == ["close", "Long", "Short"]
    assert not figure.layout.shapes


def test_labels_plot_validates_events_values_and_endpoints(label_plot_data):
    prices, labels = label_plot_data

    outside = labels.copy()
    outside.index = outside.index + pd.DateOffset(years=10)
    with pytest.raises(ValueError, match="event must be present"):
        q.plot.labels(prices, outside)

    invalid = labels.copy()
    invalid.loc[invalid.index[0], "label"] = 2
    with pytest.raises(ValueError, match="only -1, 0, or 1"):
        q.plot.labels(prices, invalid)

    bad_end = labels.copy()
    bad_end.loc[bad_end.index[0], "touch_time"] = pd.Timestamp("2030-01-01")
    with pytest.raises(ValueError, match="touch_time must be present"):
        q.plot.labels(prices, bad_end)