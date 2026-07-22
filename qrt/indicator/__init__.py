"""Stateless market measurements for research, rules, and model inputs.

Native indicators are flat under ``q.indicator``. Provider catalogs remain
explicit as ``q.indicator.talib`` and ``q.indicator.pandas_ta`` and are imported
only when accessed.
"""

from importlib import import_module

from qrt.indicator._ema import ema
from qrt.indicator._features import momentum, returns, rolling_volatility, volume_ratio
from qrt.indicator._madev import madev
from qrt.indicator._realized_volatility import (
    bipower_variation,
    log_returns,
    med_rv,
    min_rv,
    realized_quarticity,
    realized_variance,
    realized_volatility,
)
from qrt.indicator._relative_strength import (
    relative_strength,
    rs_days,
    rs_phase,
    rsma,
    rsnhbp,
)
from qrt.indicator._sma import sma
from qrt.indicator._spikes import price_spikes, volume_spike_ratio

_PROVIDERS = {"pandas_ta", "talib"}

__all__ = [
    "bipower_variation",
    "ema",
    "log_returns",
    "madev",
    "med_rv",
    "min_rv",
    "momentum",
    "pandas_ta",
    "price_spikes",
    "realized_quarticity",
    "realized_variance",
    "realized_volatility",
    "relative_strength",
    "returns",
    "rolling_volatility",
    "rs_days",
    "rs_phase",
    "rsma",
    "rsnhbp",
    "sma",
    "talib",
    "volume_ratio",
    "volume_spike_ratio",
]


def __getattr__(name: str):
    if name in _PROVIDERS:
        module = import_module(f"qrt.indicator.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | _PROVIDERS)