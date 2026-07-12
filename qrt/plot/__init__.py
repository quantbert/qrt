"""Opinionated Matplotlib plots for quantitative research.

The first helpers focus on return streams: quick column charts, equity curves,
drawdowns, and a compact performance tearsheet.
"""

from qrt.plot.core import (
	benchmark_stats,
	col,
	drawdown,
	equity,
	infer_periods_per_year,
	monthly_heatmap,
	monthly_returns,
	performance,
	plot,
	rolling_alpha,
	rolling_beta,
	rolling_sharpe,
	rolling_volatility,
	tearsheet,
)

__all__ = [
	"benchmark_stats",
	"col",
	"drawdown",
	"equity",
	"infer_periods_per_year",
	"monthly_heatmap",
	"monthly_returns",
	"performance",
	"plot",
	"rolling_alpha",
	"rolling_beta",
	"rolling_sharpe",
	"rolling_volatility",
	"tearsheet",
]
