"""Classification metrics for model evaluation."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

import numpy as np
import pandas as pd


def _classification_inputs(
    y_true: Sequence[Any] | pd.Series | np.ndarray,
    y_score: pd.DataFrame | np.ndarray,
    classes: Iterable[Any] | None,
) -> tuple[np.ndarray, np.ndarray, list[Any]]:
    labels = np.asarray(y_true)
    if labels.ndim != 1 or labels.size == 0:
        raise ValueError("y_true must be a non-empty one-dimensional array")

    if isinstance(y_score, pd.DataFrame):
        scores = y_score.to_numpy(dtype=float)
        class_labels = list(y_score.columns) if classes is None else list(classes)
    else:
        scores = np.asarray(y_score, dtype=float)
        class_labels = list(pd.unique(labels)) if classes is None else list(classes)

    if scores.ndim != 2 or scores.shape[0] != labels.size:
        raise ValueError("y_score must be a two-dimensional array with one row per target")
    if len(class_labels) != scores.shape[1]:
        raise ValueError("classes must contain one label for each y_score column")
    if len(class_labels) < 2 or len(set(class_labels)) != len(class_labels):
        raise ValueError("classes must contain at least two unique labels")
    if not np.isfinite(scores).all():
        raise ValueError("y_score must contain only finite values")
    if not pd.Index(labels).isin(class_labels).all():
        raise ValueError("every value in y_true must be present in classes")

    return labels, scores, class_labels


def _binary_roc(y_true: np.ndarray, y_score: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    positives = int(y_true.sum())
    negatives = y_true.size - positives
    if positives == 0 or negatives == 0:
        raise ValueError("each class must have at least one positive and one negative target")

    order = np.argsort(y_score, kind="mergesort")[::-1]
    sorted_true = y_true[order]
    sorted_score = y_score[order]
    distinct = np.r_[np.flatnonzero(np.diff(sorted_score)), y_true.size - 1]
    true_positives = np.r_[0, np.cumsum(sorted_true)[distinct]]
    false_positives = np.r_[0, 1 + distinct - np.cumsum(sorted_true)[distinct]]
    thresholds = np.r_[np.inf, sorted_score[distinct]]
    false_positive_rate = false_positives / negatives
    true_positive_rate = true_positives / positives
    auc = float(np.trapezoid(true_positive_rate, false_positive_rate))
    return false_positive_rate, true_positive_rate, thresholds, auc


def _binary_precision_recall(
    y_true: np.ndarray, y_score: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    positives = int(y_true.sum())
    if positives == 0:
        raise ValueError("each class must have at least one positive target")

    order = np.argsort(y_score, kind="mergesort")[::-1]
    sorted_true = y_true[order]
    sorted_score = y_score[order]
    distinct = np.r_[np.flatnonzero(np.diff(sorted_score)), y_true.size - 1]
    true_positives = np.cumsum(sorted_true)[distinct]
    predicted_positives = distinct + 1
    precision = np.r_[1.0, true_positives / predicted_positives]
    recall = np.r_[0.0, true_positives / positives]
    thresholds = np.r_[np.inf, sorted_score[distinct]]
    average_precision = float(np.sum(np.diff(recall) * precision[1:]))
    return recall, precision, thresholds, average_precision


def multiclass_roc_curve(
    y_true: Sequence[Any] | pd.Series | np.ndarray,
    y_score: pd.DataFrame | np.ndarray,
    *,
    classes: Iterable[Any] | None = None,
) -> pd.DataFrame:
    """Calculate one-vs-rest multiclass ROC curves and micro/macro averages.

    Args:
        y_true: True class labels with shape ``(n_samples,)``.
        y_score: Class scores with shape ``(n_samples, n_classes)``. DataFrame
            column names are used as class labels when ``classes`` is omitted.
        classes: Class labels in the same order as the score columns.

    Returns:
        A tidy DataFrame with ``curve``, ``class``, ``fpr``, ``tpr``,
        ``threshold``, and ``auc`` columns.
    """
    labels, scores, class_labels = _classification_inputs(y_true, y_score, classes)
    rows: list[pd.DataFrame] = []
    class_curves: list[tuple[np.ndarray, np.ndarray]] = []

    for index, label in enumerate(class_labels):
        fpr, tpr, thresholds, auc = _binary_roc(labels == label, scores[:, index])
        class_curves.append((fpr, tpr))
        rows.append(pd.DataFrame({"curve": "class", "class": label, "fpr": fpr, "tpr": tpr, "threshold": thresholds, "auc": auc}))

    encoded = np.column_stack([labels == label for label in class_labels])
    micro_fpr, micro_tpr, micro_thresholds, micro_auc = _binary_roc(encoded.ravel(), scores.ravel())
    rows.append(pd.DataFrame({"curve": "micro", "class": None, "fpr": micro_fpr, "tpr": micro_tpr, "threshold": micro_thresholds, "auc": micro_auc}))

    macro_fpr = np.unique(np.concatenate([fpr for fpr, _ in class_curves]))
    macro_tpr = np.mean([np.interp(macro_fpr, fpr, tpr) for fpr, tpr in class_curves], axis=0)
    macro_auc = float(np.trapezoid(macro_tpr, macro_fpr))
    rows.append(pd.DataFrame({"curve": "macro", "class": None, "fpr": macro_fpr, "tpr": macro_tpr, "threshold": np.nan, "auc": macro_auc}))
    return pd.concat(rows, ignore_index=True)


def multiclass_precision_recall_curve(
    y_true: Sequence[Any] | pd.Series | np.ndarray,
    y_score: pd.DataFrame | np.ndarray,
    *,
    classes: Iterable[Any] | None = None,
) -> pd.DataFrame:
    """Calculate one-vs-rest multiclass precision-recall curves and averages.

    Args:
        y_true: True class labels with shape ``(n_samples,)``.
        y_score: Class scores with shape ``(n_samples, n_classes)``. DataFrame
            column names are used as class labels when ``classes`` is omitted.
        classes: Class labels in the same order as the score columns.

    Returns:
        A tidy DataFrame with ``curve``, ``class``, ``recall``, ``precision``,
        ``threshold``, and ``average_precision`` columns.
    """
    labels, scores, class_labels = _classification_inputs(y_true, y_score, classes)
    rows: list[pd.DataFrame] = []
    class_curves: list[tuple[np.ndarray, np.ndarray]] = []
    class_average_precision: list[float] = []

    for index, label in enumerate(class_labels):
        recall, precision, thresholds, average_precision = _binary_precision_recall(labels == label, scores[:, index])
        class_curves.append((recall, precision))
        class_average_precision.append(average_precision)
        rows.append(pd.DataFrame({"curve": "class", "class": label, "recall": recall, "precision": precision, "threshold": thresholds, "average_precision": average_precision}))

    encoded = np.column_stack([labels == label for label in class_labels])
    micro_recall, micro_precision, micro_thresholds, micro_average_precision = _binary_precision_recall(encoded.ravel(), scores.ravel())
    rows.append(pd.DataFrame({"curve": "micro", "class": None, "recall": micro_recall, "precision": micro_precision, "threshold": micro_thresholds, "average_precision": micro_average_precision}))

    macro_recall = np.unique(np.concatenate([recall for recall, _ in class_curves]))
    interpolated = [np.interp(macro_recall, recall, np.maximum.accumulate(precision[::-1])[::-1]) for recall, precision in class_curves]
    macro_precision = np.mean(interpolated, axis=0)
    macro_average_precision = float(np.mean(class_average_precision))
    rows.append(pd.DataFrame({"curve": "macro", "class": None, "recall": macro_recall, "precision": macro_precision, "threshold": np.nan, "average_precision": macro_average_precision}))
    return pd.concat(rows, ignore_index=True)