from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

from alphaeval.report import CellMetrics


def compute_var(losses: pd.Series, percentile: float = 5.0) -> float:
    """Value at Risk: the loss threshold at the given percentile.

    Parameters
    ----------
    losses : pd.Series
        P&L values (negative = loss).
    percentile : float
        Lower percentile, default 5%.

    Returns
    -------
    float
        The VaR value (will be negative for real losses).
    """
    if len(losses) == 0:
        return float("nan")
    return float(np.percentile(losses, percentile))


def compute_cvar(losses: pd.Series, percentile: float = 5.0) -> float:
    """Conditional VaR (Expected Shortfall): mean of losses beyond VaR.

    Parameters
    ----------
    losses : pd.Series
        P&L values (negative = loss).
    percentile : float
        Lower percentile, default 5%.

    Returns
    -------
    float
        The CVaR value.
    """
    if len(losses) == 0:
        return float("nan")
    var = compute_var(losses, percentile)
    tail = losses[losses <= var]
    if len(tail) == 0:
        return var
    return float(tail.mean())


def compute_max_drawdown(cumulative_pnl: pd.Series) -> float:
    """Max drawdown from a cumulative P&L series."""
    if len(cumulative_pnl) == 0:
        return 0.0
    running_max = cumulative_pnl.cummax()
    drawdown = cumulative_pnl - running_max
    return float(drawdown.min())


def compute_max_dd_contribution(
    subset_losses: pd.Series,
    total_max_dd: float,
    worst_pct: float = 1.0,
) -> float:
    """Max drawdown contribution: fraction of total DD from worst N% of subset.

    Parameters
    ----------
    subset_losses : pd.Series
        P&L values for the subset (e.g. FP_Long).
    total_max_dd : float
        Max drawdown of the full strategy.
    worst_pct : float
        Bottom percentile of losses to consider, default 1%.

    Returns
    -------
    float
        Contribution ratio.
    """
    if len(subset_losses) == 0 or total_max_dd == 0:
        return float("nan")
    threshold = np.percentile(subset_losses, worst_pct)
    worst = subset_losses[subset_losses <= threshold]
    if len(worst) == 0:
        return 0.0
    return float(abs(worst.sum()) / abs(total_max_dd))


def compute_distribution_stats(returns: pd.Series) -> dict[str, float]:
    """Compute skewness and excess kurtosis."""
    if len(returns) < 3:
        return {"skewness": float("nan"), "excess_kurtosis": float("nan")}
    return {
        "skewness": float(sp_stats.skew(returns, nan_policy="omit")),
        "excess_kurtosis": float(sp_stats.kurtosis(returns, nan_policy="omit")),
    }


def compute_tail_risk(
    matrix: dict[str, CellMetrics],
    full_strategy_pnl: pd.Series,
    position_size: float,
    transaction_cost: float,
    var_percentile: float = 5.0,
    worst_pct: float = 1.0,
) -> dict[str, dict[str, Any]]:
    """Compute tail risk metrics for FP_Long and FP_Short.

    Parameters
    ----------
    matrix : dict[str, CellMetrics]
    full_strategy_pnl : pd.Series
        P&L for the full strategy (all active positions), ordered by time.
    position_size : float
    transaction_cost : float
    var_percentile : float
    worst_pct : float

    Returns
    -------
    dict with keys "FP_Long" and "FP_Short", each containing:
        var, cvar, max_dd_contribution, skewness, excess_kurtosis
    """
    total_max_dd = compute_max_drawdown(full_strategy_pnl.cumsum()) if len(full_strategy_pnl) > 0 else 0.0

    result = {}
    for cell_name, direction in [("FP_Long", 1), ("FP_Short", -1)]:
        cm = matrix.get(cell_name)
        if cm is None or cm.count == 0:
            result[cell_name] = {
                "var": float("nan"),
                "cvar": float("nan"),
                "max_dd_contribution": float("nan"),
                "skewness": float("nan"),
                "excess_kurtosis": float("nan"),
            }
            continue

        pnl = direction * cm.returns * position_size
        if transaction_cost > 0:
            pnl = pnl - transaction_cost

        dist = compute_distribution_stats(pnl)
        result[cell_name] = {
            "var": compute_var(pnl, var_percentile),
            "cvar": compute_cvar(pnl, var_percentile),
            "max_dd_contribution": compute_max_dd_contribution(pnl, total_max_dd, worst_pct),
            **dist,
        }

    return result
