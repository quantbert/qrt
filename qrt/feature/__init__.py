"""Feature engineering: transformations and wrappers around feature libraries.

Structured as a namespace of feature submodules:

    q.feature.transforms -- general-purpose feature transformations
    q.feature.talib      -- every TA-Lib indicator, pandas-friendly
    q.feature.pandas_ta  -- every pandas-ta-classic indicator

To add your own feature family, create ``qrt/feature/<name>.py`` with
functions that take a Series/DataFrame and return one, then register it
in the imports and ``__all__`` below. It becomes available as
``q.feature.<name>.*``.
"""

from qrt.feature import pandas_ta, talib, transforms

__all__ = [
    "pandas_ta",
    "talib",
    "transforms",
]
