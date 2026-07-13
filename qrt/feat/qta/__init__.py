"""qta: our own hand-rolled features, one module per feature.

To add a feature:
    1. Create ``qrt/feat/qta/_<feature>.py`` (leading underscore -- it's a
       private implementation module; the function itself stays public).
    2. Define one public function taking a Series/DataFrame and returning
       one, with the index preserved. Helpers should be prefixed with ``_``.
    3. Re-export it below (one import line + one ``__all__`` entry), so it
       is visible to IDEs and available as ``q.feat.qta.<feature>``.
"""

from qrt.feat.qta._lags import lags
from qrt.feat.qta._sma import sma

__all__ = [
    "lags",
    "sma",
]
