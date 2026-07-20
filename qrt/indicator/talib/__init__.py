"""TA-Lib indicators exposed with a pandas-friendly interface.

Every TA-Lib function is available under its usual name and accepts an
OHLCV DataFrame with lowercase columns (``open, high, low, close,
volume``) -- the frame layout returned by ``qrt.data.sources``'s ``read()``
functions (e.g. ``qrt.data.sources.yfinance.read(...)``). Indicators that
only need a price series also accept a plain Series (treated as
``close``). The datetime index is preserved on the output.

Examples:
    >>> q.indicator.talib.RSI(ohlc)                    # Series named 'rsi'
    >>> q.indicator.talib.ATR(ohlc, timeperiod=20)     # uses high/low/close
    >>> q.indicator.talib.MACD(ohlc)                   # DataFrame: macd, macdsignal, macdhist
    >>> q.indicator.talib.SMA(prices, timeperiod=20)   # Series in, Series out

Use ``dir(q.indicator.talib)`` to list all indicators, or
``help(q.indicator.talib.RSI)`` for a function's inputs and parameters.
"""

from __future__ import annotations

import pandas as pd

try:
    import talib as _talib
    from talib import abstract as _abstract
except ModuleNotFoundError as exc:
    if exc.name == "talib":
        raise ModuleNotFoundError(
            "q.indicator.talib requires the 'indicators' extra; "
            "install it with `uv add 'pyqrt[indicators]'`"
        ) from None
    raise

_FUNCTIONS = frozenset(_talib.get_functions())

__all__ = sorted(_FUNCTIONS)


def _make_indicator(name: str):
    """Build a pandas-friendly wrapper around one TA-Lib function."""

    def indicator(
        data: pd.Series | pd.DataFrame, *args, **kwargs
    ) -> pd.Series | pd.DataFrame:
        if isinstance(data, pd.Series):
            data = data.to_frame(name="close")
        # A fresh Function per call: instances are stateful and would
        # otherwise leak parameters between calls.
        out = _abstract.Function(name)(data, *args, **kwargs)
        if isinstance(out, pd.Series):
            out.name = name.lower()
        return out

    indicator.__name__ = name
    indicator.__qualname__ = name
    indicator.__doc__ = getattr(_talib, name).__doc__
    return indicator


def __getattr__(name: str):
    if name in _FUNCTIONS:
        indicator = _make_indicator(name)
        globals()[name] = indicator  # cache for subsequent lookups
        return indicator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | _FUNCTIONS)
