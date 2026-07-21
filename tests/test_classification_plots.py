import numpy as np
import pandas as pd
import pytest
from plotly.graph_objects import Figure

import qrt as q


@pytest.fixture
def perfect_multiclass_data() -> tuple[np.ndarray, pd.DataFrame]:
    y_true = np.array(["a", "b", "c", "a", "b", "c"])
    y_score = pd.DataFrame(
        {
            "a": [0.90, 0.05, 0.05, 0.80, 0.10, 0.10],
            "b": [0.05, 0.90, 0.05, 0.10, 0.80, 0.10],
            "c": [0.05, 0.05, 0.90, 0.10, 0.10, 0.80],
        }
    )
    return y_true, y_score


def test_multiclass_curves_are_perfect_for_separated_scores(perfect_multiclass_data):
    y_true, y_score = perfect_multiclass_data

    roc = q.stats.multiclass_roc_curve(y_true, y_score)
    precision_recall = q.stats.multiclass_precision_recall_curve(y_true, y_score)

    assert set(roc["curve"]) == {"class", "micro", "macro"}
    assert set(roc.loc[roc["curve"] == "class", "class"]) == {"a", "b", "c"}
    assert np.allclose(roc["auc"], 1.0)
    assert np.allclose(precision_recall["average_precision"], 1.0)


def test_multiclass_curves_handle_tied_scores_at_random_baseline():
    y_true = np.array([0, 1, 2, 0, 1, 2])
    y_score = np.ones((6, 3))

    roc = q.stats.multiclass_roc_curve(y_true, y_score, classes=[0, 1, 2])
    precision_recall = q.stats.multiclass_precision_recall_curve(y_true, y_score, classes=[0, 1, 2])

    assert np.allclose(roc["auc"], 0.5)
    assert np.allclose(precision_recall["average_precision"], 1 / 3)


def test_multiclass_plots_use_dataframe_columns_as_labels(perfect_multiclass_data):
    y_true, y_score = perfect_multiclass_data

    roc = q.plot.roc(y_true, y_score)
    precision_recall = q.plot.precision_recall(y_true, y_score)

    assert isinstance(roc, Figure)
    assert isinstance(precision_recall, Figure)
    assert [trace.name for trace in roc.data] == [
        "a (AUC=1.000)",
        "b (AUC=1.000)",
        "c (AUC=1.000)",
        "Micro average (AUC=1.000)",
        "Macro average (AUC=1.000)",
    ]
    assert tuple(roc.layout.xaxis.range) == (-0.05, 1.05)
    assert tuple(roc.layout.yaxis.range) == (-0.05, 1.05)
    assert roc.layout.xaxis.constrain == roc.layout.yaxis.constrain == "domain"
    assert roc.layout.legend.yanchor == "bottom"
    assert roc.layout.margin.t == 130
    assert tuple(precision_recall.layout.xaxis.range) == (-0.05, 1.05)
    assert tuple(precision_recall.layout.yaxis.range) == (-0.05, 1.05)
    assert precision_recall.layout.xaxis.constrain == precision_recall.layout.yaxis.constrain == "domain"
    assert precision_recall.layout.legend.yanchor == "bottom"
    assert precision_recall.layout.margin.t == 130
    assert precision_recall.layout.xaxis.title.text == "Recall"
    assert precision_recall.layout.yaxis.title.text == "Precision"


@pytest.mark.parametrize(
    ("y_true", "y_score", "classes", "message"),
    [
        ([0, 1], np.ones((3, 2)), [0, 1], "one row per target"),
        ([0, 1], np.ones((2, 2)), [0], "one label for each"),
        ([0, 2], np.ones((2, 2)), [0, 1], "present in classes"),
        ([0, 0], np.ones((2, 2)), [0, 1], "positive and one negative"),
    ],
)
def test_multiclass_roc_curve_validates_inputs(y_true, y_score, classes, message):
    with pytest.raises(ValueError, match=message):
        q.stats.multiclass_roc_curve(y_true, y_score, classes=classes)