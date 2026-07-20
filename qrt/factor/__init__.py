"""Cross-sectional characteristics and relative asset measurements.

Factor calculations compare assets; they do not choose portfolio positions.
"""

from qrt.factor._elo import compute_elo

__all__ = ["compute_elo"]