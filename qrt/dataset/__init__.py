"""Aligned datasets that bridge feature and label research with model fitting."""

from qrt.dataset._core import (
	Dataset,
	DatasetView,
	Fold,
	Partition,
	Split,
	SplitScheme,
)
from qrt.dataset._splitters import (
	PurgedTimeSeriesSplit,
	TemporalSplit,
	TimeSeriesSplit,
	audit_splits,
	split_diagnostics,
)

__all__ = [
	"Dataset",
	"DatasetView",
	"Fold",
	"Partition",
	"PurgedTimeSeriesSplit",
	"Split",
	"SplitScheme",
	"TemporalSplit",
	"TimeSeriesSplit",
	"audit_splits",
	"split_diagnostics",
]