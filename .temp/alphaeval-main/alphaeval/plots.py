from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from alphaeval.report import CellMetrics, CELL_NAMES


def _safe_import_matplotlib():
    try:
        import matplotlib.pyplot as plt

        return plt
    except ImportError:
        raise ImportError("matplotlib is required for plotting. " "Install it with: pip install alphaeval[viz]")


def _safe_import_seaborn():
    try:
        import seaborn as sns

        return sns
    except ImportError:
        raise ImportError("seaborn is required for plotting. " "Install it with: pip install alphaeval[viz]")


def plot_violin(
    matrix: dict[str, CellMetrics],
    title: str = "Forward Returns by Matrix Cell",
) -> Any:
    """Violin plot of forward returns for all 9 matrix cells.

    Returns
    -------
    matplotlib.figure.Figure
    """
    plt = _safe_import_matplotlib()
    sns = _safe_import_seaborn()

    data_rows = []
    for name in CELL_NAMES:
        cm = matrix.get(name)
        if cm and cm.count > 0:
            for r in cm.returns:
                data_rows.append({"cell": name, "return": r})

    if not data_rows:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        return fig

    plot_df = pd.DataFrame(data_rows)
    fig, ax = plt.subplots(figsize=(14, 6))
    sns.violinplot(data=plot_df, x="cell", y="return", order=CELL_NAMES, ax=ax)
    ax.set_title(title)
    ax.set_xlabel("Matrix Cell")
    ax.set_ylabel("Forward Return")
    ax.axhline(0, color="gray", linestyle="--", linewidth=0.8)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    return fig


def plot_kde_overlay(
    matrix: dict[str, CellMetrics],
    title: str = "True Positives vs False Positives (KDE)",
) -> Any:
    """Overlaid KDE of TP (correct) vs FP (incorrect) position returns.

    Returns
    -------
    matplotlib.figure.Figure
    """
    plt = _safe_import_matplotlib()
    sns = _safe_import_seaborn()

    tp_returns = []
    fp_returns = []
    for name in ["TP_Long", "TP_Short"]:
        cm = matrix.get(name)
        if cm and cm.count > 0:
            tp_returns.extend(cm.returns.tolist())
    for name in ["FP_Long", "FP_Short"]:
        cm = matrix.get(name)
        if cm and cm.count > 0:
            fp_returns.extend(cm.returns.tolist())

    fig, ax = plt.subplots(figsize=(10, 6))
    if tp_returns:
        sns.kdeplot(tp_returns, ax=ax, label="True Positives (TP)", fill=True, alpha=0.3)
    if fp_returns:
        sns.kdeplot(fp_returns, ax=ax, label="False Positives (FP)", fill=True, alpha=0.3)
    ax.set_title(title)
    ax.set_xlabel("Forward Return")
    ax.set_ylabel("Density")
    ax.axvline(0, color="gray", linestyle="--", linewidth=0.8)
    ax.legend()
    plt.tight_layout()
    return fig


def plot_time_decay(
    time_decay: dict[str, dict[int, dict[str, Any]]],
    cells: list[str] | None = None,
    title: str = "Mean Return by Horizon",
) -> Any:
    """Line chart of mean return per cell across horizons.

    Parameters
    ----------
    time_decay : dict
        Output from ``analyze_time_decay()``.
    cells : list[str] | None
        Which cells to plot. Defaults to all non-empty cells.

    Returns
    -------
    matplotlib.figure.Figure
    """
    plt = _safe_import_matplotlib()

    if cells is None:
        cells = [c for c in CELL_NAMES if c in time_decay and time_decay[c]]

    fig, ax = plt.subplots(figsize=(10, 6))
    for cell_name in cells:
        horizons_data = time_decay.get(cell_name, {})
        if not horizons_data:
            continue
        hs = sorted(horizons_data.keys())
        means = [horizons_data[h].get("mean_return", float("nan")) for h in hs]
        ax.plot(hs, means, marker="o", label=cell_name)

    ax.set_title(title)
    ax.set_xlabel("Horizon (trading days)")
    ax.set_ylabel("Mean Forward Return")
    ax.axhline(0, color="gray", linestyle="--", linewidth=0.8)
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    return fig


def plot_all(
    matrix: dict[str, CellMetrics],
    time_decay: dict[str, dict[int, dict[str, Any]]],
) -> list[Any]:
    """Generate all standard plots. Returns list of figures."""
    figures = [
        plot_violin(matrix),
        plot_kde_overlay(matrix),
    ]
    if time_decay:
        figures.append(plot_time_decay(time_decay))
    return figures
