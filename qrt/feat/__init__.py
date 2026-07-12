"""Feature engineering: indicators and wrappers around feature libraries.

Structured as a namespace of feature submodules:

    q.feat.core       -- hand-rolled features (also re-exported here: SMA, lags)
    q.feat.talib      -- every TA-Lib indicator, pandas-friendly
    q.feat.pandas_ta  -- every pandas-ta-classic indicator

To add your own feature family, create ``qrt/feat/<name>.py`` with
functions that take a Series/DataFrame and return one, then register it
in the imports and ``__all__`` below. It becomes available as
``q.feat.<name>.*``.
"""

from qrt.feat import core, pandas_ta, talib
from qrt.feat.core import SMA, lags

__all__ = [
    "core",
    "pandas_ta",
    "talib",
    # re-exported core features
    "SMA",
    "lags",
]
