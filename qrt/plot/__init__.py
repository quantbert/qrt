"""Opinionated static and interactive plots for quantitative research.

The first helpers focus on return streams: quick column charts, equity curves,
drawdowns, and compact performance tearsheets. Use :mod:`qrt.plot.interactive`
for Plotly figures with hover, zoom, and range selection. Return-stream
statistics (performance, alpha/beta, rolling diagnostics, ...) live in
:mod:`qrt.stats`.
"""

from qrt.plot import interactive
from qrt.plot.core import (
	col,
	drawdown,
	equity,
	montecarlo,
	montecarlo_distribution,
	monthly_heatmap,
	noise_test,
	plot,
	show,
	tearsheet,
	variance_test,
)

__all__ = [
	"col",
	"drawdown",
	"equity",
	"interactive",
	"montecarlo",
	"montecarlo_distribution",
	"monthly_heatmap",
	"noise_test",
	"plot",
	"show",
	"tearsheet",
	"variance_test",
]
