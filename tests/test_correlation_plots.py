import pandas as pd
import pytest
from plotly.graph_objects import Figure

import qrt as q


@pytest.fixture
def feature_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "momentum": [-1.0, -0.2, 0.3, 1.1],
            "volatility": [0.30, 0.20, 0.10, 0.40],
            "volume": [10.0, 12.0, 9.0, 15.0],
            "regime": ["risk-off", "risk-off", "risk-on", "risk-on"],
            "forward_return": [-0.04, -0.01, 0.02, 0.06],
        },
        index=pd.date_range("2025-01-01", periods=4, name="date"),
    )


def test_correlation_colors_categorical_regimes(feature_data):
    figure = q.plot.correlation(
        feature_data,
        columns=["momentum", "volatility", "volume"],
        color="regime",
        hover_data=["forward_return"],
    )

    assert isinstance(figure, Figure)
    assert {trace.name for trace in figure.data} == {"risk-off", "risk-on"}
    assert all(trace.type == "splom" for trace in figure.data)
    assert all(trace.diagonal.visible is False for trace in figure.data)
    assert all(trace.showlowerhalf is True for trace in figure.data)
    assert all(trace.showupperhalf is False for trace in figure.data)
    assert figure.layout.dragmode == "select"
    assert figure.layout.hovermode == "closest"
    assert figure.layout.margin.t == 145
    assert figure.layout.legend.y == 1.04
    assert figure.layout.legend.yanchor == "bottom"


def test_correlation_continuous_color_does_not_reserve_legend_space(feature_data):
    figure = q.plot.correlation(
        feature_data,
        columns=["momentum", "volatility"],
        color="forward_return",
    )

    assert figure.layout.margin.t == 90


def test_correlation_centers_continuous_outcomes_at_zero(feature_data):
    figure = q.plot.correlation(
        feature_data,
        columns=["momentum", "volatility"],
        color="forward_return",
        triangle="full",
    )

    assert len(figure.data) == 1
    assert figure.layout.coloraxis.cmid == 0.0
    assert figure.data[0].showlowerhalf is True
    assert figure.data[0].showupperhalf is True


def test_correlation_can_show_diagonal_and_customize_marker_contrast(feature_data):
    figure = q.plot.correlation(
        feature_data,
        columns=["momentum", "volatility"],
        diagonal=True,
        marker_size=9,
        marker_opacity=1.0,
        marker_line_width=1.2,
        marker_line_color="#111111",
    )

    trace = figure.data[0]
    assert trace.diagonal.visible is True
    assert trace.marker.size == 9
    assert trace.marker.opacity == 1.0
    assert trace.marker.line.width == 1.2
    assert trace.marker.line.color == "#111111"


def test_correlation_uses_clear_configurable_axes_and_ticks(feature_data):
    figure = q.plot.correlation(
        feature_data,
        columns=["momentum", "volatility"],
        triangle="full",
        diagonal=True,
        axis_color="#111111",
        axis_line_width=2,
        tick_length=7,
        tick_width=1.5,
    )

    for axis in (figure.layout.xaxis, figure.layout.yaxis):
        assert axis.showline is False
        assert axis.mirror is False
        assert axis.ticks == "outside"
        assert axis.tickcolor == "#111111"
        assert axis.ticklen == 7
        assert axis.tickwidth == 1.5
        assert axis.tickfont.color == "#111111"
    assert len(figure.layout.shapes) == 4
    assert all(shape.type == "rect" for shape in figure.layout.shapes)
    assert all(shape.line.color == "#111111" for shape in figure.layout.shapes)
    assert all(shape.line.width == 2 for shape in figure.layout.shapes)
    assert all(shape.layer == "between" for shape in figure.layout.shapes)


@pytest.mark.parametrize(
    ("triangle", "diagonal", "expected_frames"),
    [
        ("lower", False, 3),
        ("lower", True, 6),
        ("upper", False, 3),
        ("upper", True, 6),
        ("full", False, 6),
        ("full", True, 9),
    ],
)
def test_correlation_frames_every_visible_panel(feature_data, triangle, diagonal, expected_frames):
    figure = q.plot.correlation(
        feature_data,
        columns=["momentum", "volatility", "volume"],
        triangle=triangle,
        diagonal=diagonal,
    )

    assert len(figure.layout.shapes) == expected_frames


def test_correlation_accepts_custom_color_schemes(feature_data):
    categorical = q.plot.correlation(
        feature_data,
        columns=["momentum", "volatility"],
        color="regime",
        color_discrete_map={"risk-off": "#112233", "risk-on": "#AABBCC"},
    )
    continuous = q.plot.correlation(
        feature_data,
        columns=["momentum", "volatility"],
        color="forward_return",
        color_continuous_scale="RdBu",
    )

    assert {trace.name: trace.marker.color for trace in categorical.data} == {
        "risk-off": "#112233",
        "risk-on": "#AABBCC",
    }
    assert continuous.layout.coloraxis.colorscale[0][1] == "rgb(103,0,31)"
    assert continuous.layout.coloraxis.colorscale[-1][1] == "rgb(5,48,97)"


def test_correlation_infers_numeric_features_except_color(feature_data):
    figure = q.plot.correlation(feature_data, color="forward_return")

    assert [dimension.label for dimension in figure.data[0].dimensions] == [
        "momentum",
        "volatility",
        "volume",
    ]


@pytest.mark.parametrize(
    ("kwargs", "error", "message"),
    [
        ({"columns": ["momentum"]}, ValueError, "at least two"),
        ({"color": "missing"}, KeyError, "Color column"),
        ({"triangle": "left"}, ValueError, "triangle must be"),
        ({"marker_size": -1}, ValueError, "marker_size"),
        ({"marker_opacity": 1.1}, ValueError, "marker_opacity"),
        ({"marker_line_width": -1}, ValueError, "marker_line_width"),
        ({"axis_line_width": -1}, ValueError, "axis_line_width"),
        ({"tick_length": -1}, ValueError, "tick_length"),
        ({"tick_width": -1}, ValueError, "tick_width"),
        ({"hover_data": ["missing"]}, KeyError, "Hover columns"),
    ],
)
def test_correlation_validates_inputs(feature_data, kwargs, error, message):
    with pytest.raises(error, match=message):
        q.plot.correlation(feature_data, **kwargs)