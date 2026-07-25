import numpy as np
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
        color_by="regime",
        hover_data=["forward_return"],
    )

    assert isinstance(figure, Figure)
    assert {trace.name for trace in figure.data} == {"risk-off", "risk-on"}
    assert all(trace.type == "splom" for trace in figure.data)
    assert all(trace.diagonal.visible is True for trace in figure.data)
    assert all(trace.showlowerhalf is True for trace in figure.data)
    assert all(trace.showupperhalf is True for trace in figure.data)
    assert figure.layout.dragmode == "select"
    assert figure.layout.hovermode == "closest"
    assert figure.layout.margin.t == 145
    assert figure.layout.width == 570
    assert figure.layout.legend.y == 1.04
    assert figure.layout.legend.yanchor == "bottom"


def test_correlation_continuous_color_does_not_reserve_legend_space(feature_data):
    figure = q.plot.correlation(
        feature_data,
        columns=["momentum", "volatility"],
        color_by="forward_return",
    )

    assert figure.layout.margin.t == 90
    assert figure.layout.margin.r == 120
    assert figure.layout.width == 540


def test_correlation_supports_rectangular_and_responsive_panels(feature_data):
    rectangular = q.plot.correlation(
        feature_data,
        columns=["momentum", "volatility"],
        panel_aspect_ratio=1.5,
    )
    responsive = q.plot.correlation(
        feature_data,
        columns=["momentum", "volatility"],
        panel_aspect_ratio=None,
    )
    fixed = q.plot.correlation(
        feature_data,
        columns=["momentum", "volatility"],
        width=900,
    )

    assert rectangular.layout.width == 630
    assert responsive.layout.width is None
    assert fixed.layout.width == 900


def test_correlation_default_matrix_is_square_with_readable_cells(feature_data):
    figure = q.plot.correlation(
        feature_data,
        columns=["momentum", "volatility", "volume"],
        color_by="forward_return",
        triangle="full",
        diagonal=True,
    )

    matrix_width = figure.layout.width - figure.layout.margin.l - figure.layout.margin.r
    matrix_height = figure.layout.height - figure.layout.margin.t - figure.layout.margin.b
    assert matrix_width == matrix_height == 480


def test_correlation_centers_continuous_outcomes_at_zero(feature_data):
    figure = q.plot.correlation(
        feature_data,
        columns=["momentum", "volatility"],
        color_by="forward_return",
        triangle="full",
    )

    assert len(figure.data) == 1
    assert figure.layout.coloraxis.cmid == 0.0
    assert figure.layout.coloraxis.colorscale[0][1] == "rgb(165,0,38)"
    assert figure.layout.coloraxis.colorscale[-1][1] == "rgb(0,104,55)"
    assert figure.data[0].showlowerhalf is True
    assert figure.data[0].showupperhalf is True
    assert figure.data[0].diagonal.visible is True
    assert figure.data[0].marker.line.color == "#1F2937"


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
        color_by="regime",
        color_discrete_map={"risk-off": "#112233", "risk-on": "#AABBCC"},
    )
    continuous = q.plot.correlation(
        feature_data,
        columns=["momentum", "volatility"],
        color_by="forward_return",
        color_continuous_scale="RdBu",
    )

    assert {trace.name: trace.marker.color for trace in categorical.data} == {
        "risk-off": "#112233",
        "risk-on": "#AABBCC",
    }
    assert continuous.layout.coloraxis.colorscale[0][1] == "rgb(103,0,31)"
    assert continuous.layout.coloraxis.colorscale[-1][1] == "rgb(5,48,97)"


def test_correlation_infers_numeric_features_except_color(feature_data):
    figure = q.plot.correlation(feature_data, color_by="forward_return")

    assert [dimension.label for dimension in figure.data[0].dimensions] == [
        "momentum",
        "volatility",
        "volume",
    ]


@pytest.mark.parametrize(
    ("kwargs", "error", "message"),
    [
        ({"columns": ["momentum"]}, ValueError, "at least two"),
        ({"color_by": "missing"}, KeyError, "color_by column"),
        ({"triangle": "left"}, ValueError, "triangle must be"),
        ({"marker_size": -1}, ValueError, "marker_size"),
        ({"marker_opacity": 1.1}, ValueError, "marker_opacity"),
        ({"marker_line_width": -1}, ValueError, "marker_line_width"),
        ({"axis_line_width": -1}, ValueError, "axis_line_width"),
        ({"tick_length": -1}, ValueError, "tick_length"),
        ({"tick_width": -1}, ValueError, "tick_width"),
        ({"width": 0}, ValueError, "width"),
        ({"height": 0}, ValueError, "height"),
        ({"panel_aspect_ratio": 0}, ValueError, "panel_aspect_ratio"),
        ({"hover_data": ["missing"]}, KeyError, "Hover columns"),
    ],
)
def test_correlation_validates_inputs(feature_data, kwargs, error, message):
    with pytest.raises(error, match=message):
        q.plot.correlation(feature_data, **kwargs)


@pytest.fixture
def wide_feature_data() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    trend = rng.normal(size=240)
    risk = rng.normal(size=240)
    frame = pd.DataFrame(
        {
            "trend_a": trend + 0.05 * rng.normal(size=240),
            "trend_b": trend + 0.05 * rng.normal(size=240),
            "risk_a": risk + 0.05 * rng.normal(size=240),
            "risk_b": risk + 0.05 * rng.normal(size=240),
        },
        index=pd.date_range("2024-01-01", periods=240, name="date"),
    )
    frame["regime"] = np.where(frame["trend_a"] > 0, "risk-on", "risk-off")
    return frame


def test_correlation_heatmap_pins_scale_and_annotates_small_matrices(wide_feature_data):
    figure = q.plot.correlation_heatmap(wide_feature_data)

    trace = figure.data[0]
    assert isinstance(figure, Figure)
    assert trace.type == "heatmap"
    assert (trace.zmin, trace.zmid, trace.zmax) == (-1.0, 0.0, 1.0)
    assert trace.colorscale[0][1] == "rgb(165,0,38)"
    assert trace.colorscale[-1][1] == "rgb(0,104,55)"
    assert list(trace.x) == list(trace.y) == ["trend_a", "trend_b", "risk_a", "risk_b"]
    assert trace.colorbar.title.text == "Correlation"
    assert len(figure.layout.annotations) == 16
    assert figure.layout.yaxis.autorange == "reversed"
    assert figure.layout.yaxis.scaleanchor == "x"


def test_correlation_heatmap_excludes_non_numeric_columns(wide_feature_data):
    figure = q.plot.correlation_heatmap(wide_feature_data)

    assert "regime" not in list(figure.data[0].x)


def test_correlation_heatmap_annotations_stay_legible_on_dark_cells(wide_feature_data):
    figure = q.plot.correlation_heatmap(wide_feature_data, columns=["trend_a", "trend_b"])

    colors = {annotation.text: annotation.font.color for annotation in figure.layout.annotations}
    assert colors["1.00"] == "#F9FAFB"


@pytest.mark.parametrize(
    ("triangle", "diagonal", "expected_cells"),
    [
        ("full", True, 16),
        ("full", False, 12),
        ("lower", True, 10),
        ("lower", False, 6),
        ("upper", True, 10),
        ("upper", False, 6),
    ],
)
def test_correlation_heatmap_masks_requested_cells(wide_feature_data, triangle, diagonal, expected_cells):
    figure = q.plot.correlation_heatmap(wide_feature_data, triangle=triangle, diagonal=diagonal)

    assert np.isfinite(np.array(figure.data[0].z, dtype=float)).sum() == expected_cells
    assert figure.data[0].hoverongaps is False


def test_correlation_heatmap_clusters_similar_features_together(wide_feature_data):
    ordered = q.plot.correlation_heatmap(wide_feature_data, cluster=True)

    names = list(ordered.data[0].x)
    assert abs(names.index("trend_a") - names.index("trend_b")) == 1
    assert abs(names.index("risk_a") - names.index("risk_b")) == 1


def test_correlation_heatmap_hides_values_when_matrix_is_dense():
    rng = np.random.default_rng(1)
    dense = pd.DataFrame(rng.normal(size=(120, 20)), columns=[f"feature_{i:02d}" for i in range(20)])

    inferred = q.plot.correlation_heatmap(dense)
    forced = q.plot.correlation_heatmap(dense, show_values=True)

    assert inferred.layout.annotations == ()
    assert len(forced.layout.annotations) == 400


def test_correlation_heatmap_supports_rank_methods_and_labels(wide_feature_data):
    pearson = q.plot.correlation_heatmap(wide_feature_data, method="pearson")
    spearman = q.plot.correlation_heatmap(
        wide_feature_data,
        method="spearman",
        labels={"trend_a": "Trend A"},
        colorbar_label="Spearman",
    )

    assert list(spearman.data[0].x)[0] == "Trend A"
    assert spearman.data[0].colorbar.title.text == "Spearman"
    assert np.array(spearman.data[0].z)[0][1] != np.array(pearson.data[0].z)[0][1]


def test_correlation_heatmap_sizes_cells_squarely(wide_feature_data):
    figure = q.plot.correlation_heatmap(wide_feature_data)
    fixed = q.plot.correlation_heatmap(wide_feature_data, height=700, width=800)

    matrix_width = figure.layout.width - figure.layout.margin.l - figure.layout.margin.r
    matrix_height = figure.layout.height - figure.layout.margin.t - figure.layout.margin.b
    assert matrix_width == matrix_height == 320
    assert (fixed.layout.height, fixed.layout.width) == (700, 800)


@pytest.mark.parametrize(
    ("kwargs", "error", "message"),
    [
        ({"columns": ["trend_a"]}, ValueError, "at least two"),
        ({"method": "linear"}, ValueError, "method must be"),
        ({"triangle": "left"}, ValueError, "triangle must be"),
        ({"min_periods": 0}, ValueError, "min_periods"),
        ({"cell_size": 0}, ValueError, "cell_size"),
        ({"text_size": -1}, ValueError, "text_size"),
        ({"width": 0}, ValueError, "width"),
        ({"height": 0}, ValueError, "height"),
    ],
)
def test_correlation_heatmap_validates_inputs(wide_feature_data, kwargs, error, message):
    with pytest.raises(error, match=message):
        q.plot.correlation_heatmap(wide_feature_data, **kwargs)


def test_correlation_heatmap_rejects_non_dataframe():
    with pytest.raises(TypeError, match="DataFrame"):
        q.plot.correlation_heatmap(pd.Series([1.0, 2.0, 3.0]))