from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


# Canonical cell names for the 3x3 matrix
CELL_NAMES = [
    "TP_Long",
    "FN_Up",
    "FP_Short",
    "CD_Long",
    "TN",
    "CD_Short",
    "FP_Long",
    "FN_Down",
    "TP_Short",
]


@dataclass
class CellMetrics:
    """Metrics for a single cell of the 3x3 confusion matrix."""

    name: str
    count: int = 0
    total_pnl: float = 0.0
    avg_pnl: float = 0.0
    max_profit: float = 0.0
    max_loss: float = 0.0
    returns: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))

    def __repr__(self) -> str:
        return f"CellMetrics({self.name}: n={self.count}, " f"total={self.total_pnl:+.4f}, avg={self.avg_pnl:+.4f})"


@dataclass
class EvalReport:
    """Full evaluation report returned by evaluate()."""

    # 3x3 matrix: cell_name -> CellMetrics
    matrix: dict[str, CellMetrics] = field(default_factory=dict)

    # Aggregate metrics
    metrics: dict[str, Any] = field(default_factory=dict)

    # Tail risk metrics
    tail_risk: dict[str, Any] = field(default_factory=dict)

    # Time-decay: {cell_name: {horizon: {metric_name: value}}}
    time_decay: dict[str, dict[int, dict[str, Any]]] = field(default_factory=dict)

    # Config used
    config: dict[str, Any] = field(default_factory=dict)

    # Underlying data with cell assignments
    data: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(), repr=False)

    def summary(self) -> str:
        """Return an sklearn-style text summary."""
        lines: list[str] = []
        lines.append("=" * 72)
        lines.append("alphaeval — Financial Confusion Matrix Report")
        lines.append("=" * 72)

        # Config
        cfg = self.config
        lines.append(
            f"Horizon: {cfg.get('primary_horizon', '?')}d | "
            f"Flat threshold: {cfg.get('flat_threshold', '?')} | "
            f"Return type: {cfg.get('return_type', '?')} | "
            f"Txn cost: {cfg.get('transaction_cost', 0)}"
        )
        lines.append("")

        # Matrix counts
        names = cfg.get("target_names", ["BUY", "HOLD", "SELL"])
        buy_label, hold_label, sell_label = names[0], names[1], names[2]
        lines.append(f"{'':>12} {buy_label:>14} {hold_label:>14} {sell_label:>14}")
        lines.append("-" * 56)

        rows = [
            ("Up", ["TP_Long", "FN_Up", "FP_Short"]),
            ("Flat", ["CD_Long", "TN", "CD_Short"]),
            ("Down", ["FP_Long", "FN_Down", "TP_Short"]),
        ]
        for row_label, cells in rows:
            counts = []
            for c in cells:
                cm = self.matrix.get(c)
                counts.append(str(cm.count) if cm else "0")
            lines.append(f"{row_label:>12} {counts[0]:>14} {counts[1]:>14} {counts[2]:>14}")

        lines.append("")

        # Per-cell P&L summary
        lines.append("Per-Cell P&L Summary:")
        lines.append(f"  {'Cell':<12} {'Count':>7} {'Total P&L':>12} {'Avg P&L':>12} {'Max Profit':>12} {'Max Loss':>12}")
        lines.append("  " + "-" * 68)
        for name in CELL_NAMES:
            cm = self.matrix.get(name)
            if cm and cm.count > 0:
                lines.append(f"  {cm.name:<12} {cm.count:>7} {cm.total_pnl:>+12.4f} " f"{cm.avg_pnl:>+12.4f} {cm.max_profit:>+12.4f} {cm.max_loss:>+12.4f}")

        lines.append("")

        # Aggregate metrics
        m = self.metrics
        lines.append("Aggregate Metrics:")
        if "expectancy_long" in m:
            lines.append(f"  Expectancy (Long):  {m['expectancy_long']:+.6f}")
        if "expectancy_short" in m:
            lines.append(f"  Expectancy (Short): {m['expectancy_short']:+.6f}")
        if "profit_factor" in m:
            pf = m["profit_factor"]
            lines.append(f"  Profit Factor:      {pf:.4f}" if pf is not None else "  Profit Factor:      N/A (no losses)")
        if "return_weighted_accuracy" in m:
            lines.append(f"  Return-Weighted Acc: {m['return_weighted_accuracy']:.4f}")

        lines.append("")

        # Tail risk
        if self.tail_risk:
            lines.append("Tail Risk (False Positives):")
            for side in ["FP_Long", "FP_Short"]:
                tr = self.tail_risk.get(side, {})
                if tr:
                    lines.append(f"  {side}:")
                    lines.append(f"    VaR (5%):    {tr.get('var', float('nan')):+.6f}")
                    lines.append(f"    CVaR (5%):   {tr.get('cvar', float('nan')):+.6f}")
                    lines.append(f"    Skewness:    {tr.get('skewness', float('nan')):.4f}")
                    lines.append(f"    Ex. Kurtosis:{tr.get('excess_kurtosis', float('nan')):.4f}")
                    lines.append(f"    Max DD Contr:{tr.get('max_dd_contribution', float('nan')):.4f}")
            lines.append("")

        # Time-decay summary
        if self.time_decay:
            horizons = sorted({h for cell_data in self.time_decay.values() for h in cell_data})
            lines.append("Time-Decay (mean return per cell × horizon):")
            header = f"  {'Cell':<12}" + "".join(f"{'t+' + str(h):>10}" for h in horizons)
            lines.append(header)
            lines.append("  " + "-" * (12 + 10 * len(horizons)))
            for name in CELL_NAMES:
                if name in self.time_decay:
                    vals = []
                    for h in horizons:
                        mean_r = self.time_decay[name].get(h, {}).get("mean_return", float("nan"))
                        vals.append(f"{mean_r:>+10.4f}")
                    lines.append(f"  {name:<12}" + "".join(vals))
            lines.append("")

        lines.append("=" * 72)
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Return the full report as a nested dict."""
        return {
            "matrix": {
                name: {
                    "count": cm.count,
                    "total_pnl": cm.total_pnl,
                    "avg_pnl": cm.avg_pnl,
                    "max_profit": cm.max_profit,
                    "max_loss": cm.max_loss,
                }
                for name, cm in self.matrix.items()
            },
            "metrics": dict(self.metrics),
            "tail_risk": dict(self.tail_risk),
            "time_decay": {cell: {h: dict(hm) for h, hm in horizons.items()} for cell, horizons in self.time_decay.items()},
            "config": dict(self.config),
        }

    def __repr__(self) -> str:
        total = sum(cm.count for cm in self.matrix.values())
        return f"EvalReport(observations={total}, cells={len(self.matrix)})"

    def __str__(self) -> str:
        return self.summary()
