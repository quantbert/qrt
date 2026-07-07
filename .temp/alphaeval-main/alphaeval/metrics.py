from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from alphaeval.report import CellMetrics


def _expectancy(
    pnl: pd.Series,
) -> float:
    """Compute expectancy: (win_rate * avg_win) - (loss_rate * avg_loss)."""
    if len(pnl) == 0:
        return 0.0
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    n = len(pnl)
    win_rate = len(wins) / n if n else 0.0
    loss_rate = len(losses) / n if n else 0.0
    avg_win = float(wins.mean()) if len(wins) > 0 else 0.0
    avg_loss = float(losses.mean().item()) if len(losses) > 0 else 0.0
    return win_rate * avg_win - loss_rate * abs(avg_loss)


def compute_aggregate_metrics(
    matrix: dict[str, CellMetrics],
    position_size: float,
    transaction_cost: float,
) -> dict[str, Any]:
    """Compute aggregate trading metrics from the confusion matrix.

    Returns dict with keys:
    - expectancy_long, expectancy_short
    - profit_factor
    - return_weighted_accuracy
    - gross_profit, gross_loss
    - win_count, loss_count, total_active
    """
    # Collect P&L for long and short positions
    long_cells = ["TP_Long", "FP_Long", "CD_Long"]
    short_cells = ["TP_Short", "FP_Short", "CD_Short"]

    def _cell_pnl(cell: CellMetrics, direction: int) -> pd.Series:
        """Recompute P&L from stored returns."""
        if cell.count == 0:
            return pd.Series(dtype=float)
        pnl = direction * cell.returns * position_size
        if transaction_cost > 0:
            pnl = pnl - transaction_cost
        return pnl

    long_pnl_parts = []
    for name in long_cells:
        cm = matrix.get(name)
        if cm and cm.count > 0:
            long_pnl_parts.append(_cell_pnl(cm, direction=1))
    long_pnl = pd.concat(long_pnl_parts) if long_pnl_parts else pd.Series(dtype=float)

    short_pnl_parts = []
    for name in short_cells:
        cm = matrix.get(name)
        if cm and cm.count > 0:
            short_pnl_parts.append(_cell_pnl(cm, direction=-1))
    short_pnl = pd.concat(short_pnl_parts) if short_pnl_parts else pd.Series(dtype=float)

    all_active_pnl = pd.concat([long_pnl, short_pnl]) if len(long_pnl) + len(short_pnl) > 0 else pd.Series(dtype=float)

    # Expectancy
    expectancy_long = _expectancy(long_pnl)
    expectancy_short = _expectancy(short_pnl)

    # Profit Factor
    gross_profit = float(all_active_pnl[all_active_pnl > 0].sum()) if len(all_active_pnl) > 0 else 0.0
    gross_loss = float(all_active_pnl[all_active_pnl < 0].sum().item()) if len(all_active_pnl) > 0 else 0.0

    if gross_loss != 0:
        profit_factor = gross_profit / abs(gross_loss)
    else:
        profit_factor = None  # No losses

    # Return-Weighted Accuracy
    # Correct = TP_Long + TP_Short. All active = all Buy + Sell predictions.
    correct_abs_returns = 0.0
    all_abs_returns = 0.0
    for name in ["TP_Long", "TP_Short"]:
        cm = matrix.get(name)
        if cm and cm.count > 0:
            correct_abs_returns += float(cm.returns.abs().sum())

    for name in long_cells + short_cells:
        cm = matrix.get(name)
        if cm and cm.count > 0:
            all_abs_returns += float(cm.returns.abs().sum())

    rwa = correct_abs_returns / all_abs_returns if all_abs_returns > 0 else 0.0

    return {
        "expectancy_long": expectancy_long,
        "expectancy_short": expectancy_short,
        "profit_factor": profit_factor,
        "return_weighted_accuracy": rwa,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "win_count": int((all_active_pnl > 0).sum()) if len(all_active_pnl) > 0 else 0,
        "loss_count": int((all_active_pnl < 0).sum()) if len(all_active_pnl) > 0 else 0,
        "total_active": len(all_active_pnl),
    }
