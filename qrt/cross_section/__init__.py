"""Cross-sectional characteristics and relative asset measurements.

Factor calculations compare assets; they do not choose portfolio positions.
"""

from qrt.cross_section._elo import compute_elo
from qrt.cross_section._group_weighted_return import group_weighted_return

__all__ = ["compute_elo", "group_weighted_return"]