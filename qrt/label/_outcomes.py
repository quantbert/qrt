"""Outcome transformations shared by labeling workflows."""

from __future__ import annotations

from numbers import Integral

import numpy as np
import pandas as pd

from qrt.label._validation import (
    aligned_numeric_values,
    finite_number,
    numeric_series,
    validate_index,
)


def meta_label(
    returns: pd.Series,
    side: pd.Series,
    *,
    threshold: float | pd.Series = 0.0,
) -> pd.Series:
    """Label whether a proposed trading side produces a positive outcome.

    Args:
        returns: Realized underlying returns.
        side: Aligned directional predictions in {-1, 0, 1}. Zero represents
            no proposed trade and always receives label 0.
        threshold: Non-negative scalar or aligned minimum side-adjusted return.

    Returns:
        Nullable integer Series containing 1 for accepted sides and 0 for
        rejected sides. Missing inputs remain missing.
    """
    realized = numeric_series(returns, "returns", allow_missing=True)
    directions = numeric_series(side, "side", allow_missing=True)
    if not directions.index.equals(realized.index):
        raise ValueError("side index must match returns index")
    if not np.isin(directions.dropna().to_numpy(), [-1.0, 0.0, 1.0]).all():
        raise ValueError("side must contain only -1, 0, or 1")

    boundaries = aligned_numeric_values(
        threshold,
        realized.index,
        "threshold",
        allow_missing=True,
        non_negative=True,
    )
    valid = realized.notna() & directions.notna() & boundaries.notna()
    labels = pd.Series(pd.NA, index=realized.index, dtype="Int8", name="meta_label")
    adjusted = realized * directions
    labels.loc[valid] = adjusted.loc[valid].gt(boundaries.loc[valid]).astype("Int8")
    return labels


def prune_labels(
    labels: pd.Series,
    *,
    min_fraction: float = 0.05,
    min_classes: int = 2,
) -> tuple[pd.Series, pd.DataFrame]:
    """Iteratively remove classes below a minimum sample fraction.

    Fractions are recomputed after each removal. Pruning stops when every
    remaining class meets ``min_fraction`` or only ``min_classes`` remain, so a
    classification target is not silently collapsed to one class by default.
    Tied rare classes are removed in first-observed order.

    Args:
        labels: Ordered target labels without missing values.
        min_fraction: Minimum class fraction in the interval (0, 1].
        min_classes: Minimum number of classes to preserve.

    Returns:
        A pair containing the filtered labels and a class-level audit DataFrame
        with initial/final counts and fractions, removal status, and drop step.
    """
    if not isinstance(labels, pd.Series):
        raise TypeError("labels must be a pandas Series")
    validate_index(labels.index, "labels index")
    if labels.isna().any():
        raise ValueError("labels must not contain missing values")
    minimum = finite_number(min_fraction, "min_fraction")
    if minimum <= 0 or minimum > 1:
        raise ValueError("min_fraction must be greater than 0 and at most 1")
    if (
        not isinstance(min_classes, Integral)
        or isinstance(min_classes, bool)
        or min_classes < 1
    ):
        raise ValueError("min_classes must be a positive integer")

    classes = pd.Index(
        pd.unique(labels),
        name="label",
        tupleize_cols=False,
    )
    initial_counts = labels.value_counts(sort=False).reindex(classes, fill_value=0)
    retained = labels.copy()
    drop_steps: dict[object, int] = {}
    class_order = {label: position for position, label in enumerate(classes)}

    while retained.nunique() > int(min_classes):
        counts = retained.value_counts(sort=False)
        fractions = counts / len(retained)
        rare = fractions[fractions < minimum]
        if rare.empty:
            break
        minimum_count = rare.min()
        tied = rare.index[rare.eq(minimum_count)]
        rarest = min(tied, key=class_order.__getitem__)
        drop_steps[rarest] = len(drop_steps) + 1
        retained = retained[retained.ne(rarest)]

    final_counts = retained.value_counts(sort=False).reindex(classes, fill_value=0)
    final_total = len(retained)
    report = pd.DataFrame(
        {
            "initial_count": initial_counts.astype("int64"),
            "initial_fraction": initial_counts / len(labels) if len(labels) else 0.0,
            "final_count": final_counts.astype("int64"),
            "final_fraction": final_counts / final_total if final_total else 0.0,
            "dropped": classes.isin(drop_steps),
            "drop_step": pd.array(
                [drop_steps.get(label, pd.NA) for label in classes],
                dtype="Int64",
            ),
        },
        index=classes,
    )
    return retained, report