"""qta: our own hand-rolled features, one module per feature.

To add a feature:
    1. Create ``qrt/feat/qta/<feature>.py`` (lowercase file name).
    2. Define one public function taking a Series/DataFrame and returning
       one, with the index preserved. Helpers should be prefixed with ``_``.
    3. Re-export it below (one import line + one ``__all__`` entry), so it
       is visible to IDEs and available as ``q.feat.qta.<feature>``.
"""

from qrt.feat.qta.lags import lags
from qrt.feat.qta.sma import sma

__all__ = [
    "lags",
    "sma",
]
