"""pandas-ta-classic indicators exposed under the qrt feature namespace.

Every pandas-ta-classic indicator is available under its usual (lowercase)
name and accepts an OHLCV DataFrame with lowercase columns (``open, high,
low, close, volume``) -- the frame layout returned by ``qrt.data.sources``'s
``read()`` functions (e.g. ``qrt.data.sources.yfinance.read(...)``).
Indicators that only need a price series also accept a plain Series
(treated as ``close``). The datetime index is preserved and outputs keep
pandas-ta's parameterised names (e.g. ``RSI_14``, ``MACD_12_26_9``).

Examples:
    >>> q.feat.pandas_ta.rsi(ohlc)                  # Series 'RSI_14'
    >>> q.feat.pandas_ta.bbands(ohlc, length=20)    # DataFrame BBL/BBM/BBU...
    >>> q.feat.pandas_ta.cdl_pattern(ohlc, name="doji")
    >>> q.feat.pandas_ta.rsi(prices)                # Series in, Series out

Use ``dir(q.feat.pandas_ta)`` to list all indicators, or
``help(q.feat.pandas_ta.rsi)`` for a function's parameters.
"""

from __future__ import annotations

import pandas as pd
import pandas_ta_classic as _pta

_FUNCTIONS = frozenset(
    name for names in _pta.Category.values() for name in names
)

__all__ = sorted(_FUNCTIONS)


def _make_indicator(name: str):
    """Build a wrapper dispatching to the pandas-ta ``df.ta`` accessor."""

    def indicator(
        data: pd.Series | pd.DataFrame, *args, **kwargs
    ) -> pd.Series | pd.DataFrame:
        if isinstance(data, pd.Series):
            data = data.to_frame(name="close")
        return getattr(data.ta, name)(*args, **kwargs)

    indicator.__name__ = name
    indicator.__qualname__ = name
    indicator.__doc__ = getattr(_pta, name).__doc__
    return indicator


def __getattr__(name: str):
    if name in _FUNCTIONS:
        indicator = _make_indicator(name)
        globals()[name] = indicator  # cache for subsequent lookups
        return indicator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | _FUNCTIONS)
