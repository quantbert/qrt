"""General-purpose feature transformations, one module per transform.

To add a transform:
    1. Create ``qrt/feature/transforms/_<transform>.py`` (leading underscore --
       it is a private implementation module; the function itself stays public).
    2. Define one public function taking a Series/DataFrame and returning
       one, with the index preserved. Helpers should be prefixed with ``_``.
    3. Re-export it below (one import line + one ``__all__`` entry), so it
       is visible to IDEs and available as ``q.feature.transforms.<transform>``.
"""

from qrt.feature.transforms._lags import lags
from qrt.feature.transforms._pct_rank import pct_rank
from qrt.feature.transforms._sma import sma

__all__ = [
    "lags",
    "pct_rank",
    "sma",
]