"""Point-in-time investment intent derived from scores, models, or rules.

Signals use only information available at each row. They express desired
direction or exposure; they are not future-aware training targets, portfolio
allocations, orders, or simulated fills.
"""

from qrt.signal._dynamics import (
	cooldown,
	decay,
	delay,
	hold,
	limit_turnover,
	target_exposure,
)
from qrt.signal._scores import (
	combine,
	hysteresis,
	neutralize,
	normalize,
	select,
	threshold,
)
from qrt.signal._validation import as_signal

__all__ = [
	"as_signal",
	"combine",
	"cooldown",
	"decay",
	"delay",
	"hold",
	"hysteresis",
	"limit_turnover",
	"neutralize",
	"normalize",
	"select",
	"target_exposure",
	"threshold",
]