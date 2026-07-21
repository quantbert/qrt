"""Leakage-explicit target construction for financial machine learning.

Labeling functions intentionally inspect observations after each event. They
produce model targets and must not be used as point-in-time input features.
"""

from qrt.label._barriers import fixed_horizon, triple_barrier, vertical_barriers
from qrt.label._events import cusum_filter
from qrt.label._outcomes import meta_label, prune_labels
from qrt.label._trend import trend_scanning
from qrt.label._weights import (
	average_uniqueness,
	class_balance_weights,
	combine_weights,
	concurrency,
	indicator_matrix,
	purging_metadata,
	sample_weights,
	sequential_bootstrap,
	time_decay,
)

__all__ = [
	"average_uniqueness",
	"class_balance_weights",
	"combine_weights",
	"concurrency",
	"cusum_filter",
	"fixed_horizon",
	"indicator_matrix",
	"meta_label",
	"prune_labels",
	"purging_metadata",
	"sample_weights",
	"sequential_bootstrap",
	"time_decay",
	"trend_scanning",
	"triple_barrier",
	"vertical_barriers",
]