from __future__ import annotations

import numpy as np
import pandas as pd

from alphaeval.report import CellMetrics

# Mapping from (actual_direction, y_pred) -> cell name
_CELL_MAP: dict[tuple[str, int], str] = {
    ("Up", 1): "TP_Long",
    ("Up", 0): "FN_Up",
    ("Up", -1): "FP_Short",
    ("Flat", 1): "CD_Long",
    ("Flat", 0): "TN",
    ("Flat", -1): "CD_Short",
    ("Down", 1): "FP_Long",
    ("Down", 0): "FN_Down",
    ("Down", -1): "TP_Short",
}


def classify_actual(
    forward_returns: pd.Series,
    flat_threshold: float,
) -> pd.Series:
    """Classify forward returns into Up / Flat / Down.

    Parameters
    ----------
    forward_returns : pd.Series
        Continuous forward returns.
    flat_threshold : float
        Returns in (-threshold, +threshold) are Flat.

    Returns
    -------
    pd.Series
        Categorical series with values "Up", "Flat", "Down".
    """
    conditions = [
        forward_returns > flat_threshold,
        forward_returns < -flat_threshold,
    ]
    choices = ["Up", "Down"]
    return pd.Series(
        np.select(conditions, choices, default="Flat"),
        index=forward_returns.index,
        name="actual_direction",
    )


def assign_cells(
    actual_direction: pd.Series,
    y_pred: pd.Series,
) -> pd.Series:
    """Assign each observation to one of the 9 matrix cells.

    Parameters
    ----------
    actual_direction : pd.Series
        "Up", "Flat", or "Down" per observation.
    y_pred : pd.Series
        Prediction: 1, 0, or -1.

    Returns
    -------
    pd.Series
        Cell name per observation.
    """
    return pd.Series(
        [_CELL_MAP[(direction, pred)] for direction, pred in zip(actual_direction, y_pred)],
        index=actual_direction.index,
        name="cell",
    )


def compute_pnl(
    forward_returns: pd.Series,
    y_pred: pd.Series,
    position_size: float,
    transaction_cost: float,
) -> pd.Series:
    """Compute P&L for each observation.

    - Buy (1): pnl = +return * position_size - txn_cost
    - Sell (-1): pnl = -return * position_size - txn_cost
    - Hold (0): pnl = 0 (no position taken)
    """
    direction = y_pred.astype(float)
    active = direction != 0
    pnl = direction * forward_returns * position_size
    pnl[active] -= transaction_cost
    return pnl.rename("pnl")


def build_matrix(
    df: pd.DataFrame,
    fwd_col: str,
    flat_threshold: float,
    position_size: float,
    transaction_cost: float,
) -> dict[str, CellMetrics]:
    """Build the 3x3 confusion matrix with per-cell metrics.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain ``fwd_col`` and ``y_pred`` columns.
    fwd_col : str
        Name of the forward return column to use (e.g. "fwd_return_1").
    flat_threshold : float
    position_size : float
    transaction_cost : float

    Returns
    -------
    dict[str, CellMetrics]
        Mapping of cell name to its metrics.
    """
    fwd = df[fwd_col]
    y_pred = df["y_pred"]

    actual_dir = classify_actual(fwd, flat_threshold)
    cells = assign_cells(actual_dir, y_pred)
    pnl = compute_pnl(fwd, y_pred, position_size, transaction_cost)

    result: dict[str, CellMetrics] = {}
    for cell_name in _CELL_MAP.values():
        mask = cells == cell_name
        cell_pnl = pnl[mask]
        cell_returns = fwd[mask]
        n = int(mask.sum())

        cm = CellMetrics(
            name=cell_name,
            count=n,
            returns=cell_returns.reset_index(drop=True),
        )
        if n > 0:
            cm.total_pnl = float(cell_pnl.sum())
            cm.avg_pnl = float(cell_pnl.mean())
            cm.max_profit = float(cell_pnl.max())
            cm.max_loss = float(cell_pnl.min())

        result[cell_name] = cm

    return result
