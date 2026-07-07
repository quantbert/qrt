from __future__ import annotations

from typing import Any

import pandas as pd

from alphaeval.forward_returns import compute_forward_returns
from alphaeval.matrix import build_matrix, compute_pnl
from alphaeval.metrics import compute_aggregate_metrics
from alphaeval.tail_risk import compute_tail_risk
from alphaeval.time_decay import analyze_time_decay
from alphaeval.report import EvalReport


def evaluate(
    data: pd.DataFrame,
    return_horizons: list[int] | None = None,
    flat_threshold: float = 0.005,
    return_type: str = "simple",
    benchmark: pd.Series | None = None,
    target_names: list[str] | None = None,
    position_size: float = 1.0,
    transaction_cost: float = 0.0,
) -> EvalReport:
    """Evaluate a Buy/Hold/Sell model against forward returns.

    Parameters
    ----------
    data : pd.DataFrame
        Required columns: datetime, instrument_id, return, y_pred.
    return_horizons : list[int], optional
        Forward return horizons in trading days. Default ``[1, 5, 10]``.
    flat_threshold : float
        Returns in ``(-threshold, +threshold)`` classified as Flat.
    return_type : str
        ``'simple'`` (compound) or ``'log'`` (additive).
    benchmark : pd.Series | None
        Optional benchmark returns (reserved for future use).
    target_names : list[str] | None
        Display names for predictions 1, 0, -1. Default ``['BUY', 'HOLD', 'SELL']``.
    position_size : float
        Equal-weight position size multiplier.
    transaction_cost : float
        Round-trip transaction cost per trade (fraction).

    Returns
    -------
    EvalReport
    """
    if return_horizons is None:
        return_horizons = [1, 5, 10]
    if target_names is None:
        target_names = ["BUY", "HOLD", "SELL"]

    # Step 1: Compute forward returns
    df = compute_forward_returns(data, return_horizons, return_type)

    # Step 2: Build confusion matrix at primary horizon
    primary_horizon = return_horizons[0]
    primary_col = f"fwd_return_{primary_horizon}"

    matrix = build_matrix(
        df,
        fwd_col=primary_col,
        flat_threshold=flat_threshold,
        position_size=position_size,
        transaction_cost=transaction_cost,
    )

    # Step 3: Aggregate metrics
    metrics = compute_aggregate_metrics(matrix, position_size, transaction_cost)

    # Step 4: Tail risk
    # Build full strategy P&L (ordered by time) for max drawdown calc
    active_mask = df["y_pred"] != 0
    full_pnl = compute_pnl(df[primary_col], df["y_pred"], position_size, transaction_cost)
    # Keep only active positions, ordered by datetime
    active_pnl = full_pnl[active_mask].reset_index(drop=True)

    tail_risk = compute_tail_risk(
        matrix,
        full_strategy_pnl=active_pnl,
        position_size=position_size,
        transaction_cost=transaction_cost,
    )

    # Step 5: Time-decay analysis (across all horizons)
    time_decay = analyze_time_decay(
        df,
        horizons=return_horizons,
        flat_threshold=flat_threshold,
        position_size=position_size,
        transaction_cost=transaction_cost,
    )

    # Step 6: Assemble report
    config = {
        "return_horizons": return_horizons,
        "primary_horizon": primary_horizon,
        "flat_threshold": flat_threshold,
        "return_type": return_type,
        "target_names": target_names,
        "position_size": position_size,
        "transaction_cost": transaction_cost,
    }

    return EvalReport(
        matrix=matrix,
        metrics=metrics,
        tail_risk=tail_risk,
        time_decay=time_decay,
        config=config,
        data=df,
    )
