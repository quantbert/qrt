from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from alphaeval.matrix import classify_actual, assign_cells
from alphaeval.report import CELL_NAMES


def analyze_time_decay(
    df: pd.DataFrame,
    horizons: list[int],
    flat_threshold: float,
    position_size: float,
    transaction_cost: float,
) -> dict[str, dict[int, dict[str, Any]]]:
    """Compute per-cell metrics at each forward return horizon.

    Parameters
    ----------
    df : pd.DataFrame
        Must have columns ``y_pred`` and ``fwd_return_{h}`` for each horizon.
    horizons : list[int]
    flat_threshold : float
    position_size : float
    transaction_cost : float

    Returns
    -------
    dict
        ``{cell_name: {horizon: {count, mean_return, total_pnl, ...}}}``
    """
    result: dict[str, dict[int, dict[str, Any]]] = {}

    for h in horizons:
        col = f"fwd_return_{h}"
        if col not in df.columns:
            continue

        subset = df.dropna(subset=[col])
        if len(subset) == 0:
            continue

        fwd = subset[col]
        y_pred = subset["y_pred"]
        actual = classify_actual(fwd, flat_threshold)
        cells = assign_cells(actual, y_pred)

        direction = y_pred.astype(float)
        active = direction != 0
        pnl = direction * fwd * position_size
        pnl[active] -= transaction_cost

        for cell_name in CELL_NAMES:
            mask = cells == cell_name
            n = int(mask.sum())
            cell_fwd = fwd[mask]
            cell_pnl = pnl[mask]

            if cell_name not in result:
                result[cell_name] = {}

            metrics: dict[str, Any] = {
                "count": n,
                "mean_return": float(cell_fwd.mean()) if n > 0 else float("nan"),
                "total_pnl": float(cell_pnl.sum()) if n > 0 else 0.0,
                "avg_pnl": float(cell_pnl.mean()) if n > 0 else float("nan"),
            }
            result[cell_name][h] = metrics

    return result
