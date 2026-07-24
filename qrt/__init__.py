"""Quant Research Tools (qrt).

Usage:
    import qrt as q
"""

from __future__ import annotations

import importlib
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING, Any

# Preserve lazy runtime imports while exposing concrete namespace types to static
# analyzers; otherwise, __getattr__ makes every q.<namespace> resolve as Any.
if TYPE_CHECKING:
    from . import (
        ai as ai,
        bt as bt,
        calendar as calendar,
        cross_section as cross_section,
        data as data,
        dataset as dataset,
        env as env,
        experiment as experiment,
        gym as gym,
        indicator as indicator,
        label as label,
        model as model,
        plot as plot,
        portfolio as portfolio,
        ray as ray,
        signal as signal,
        stats as stats,
        transform as transform,
        utils as utils,
    )
    from .utils import log as log
    from .utils import set_seed as set_seed


_NAMESPACES = {
    "ai",
    "bt",
    "calendar",
    "cross_section",
    "data",
    "dataset",
    "env",
    "experiment",
    "gym",
    "indicator",
    "label",
    "model",
    "plot",
    "portfolio",
    "ray",
    "signal",
    "stats",
    "transform",
    "utils",
}
_UTILITY_EXPORTS = {"log", "set_seed"}

try:
    __version__ = version("pyqrt")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"


def __getattr__(name: str) -> Any:
    if name in _NAMESPACES:
        value = importlib.import_module(f"qrt.{name}")
    elif name in _UTILITY_EXPORTS:
        value = getattr(importlib.import_module("qrt.utils"), name)
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | _NAMESPACES | _UTILITY_EXPORTS)

__all__ = [
    "ai",
    "bt",
    "calendar",
    "cross_section",
    "data",
    "dataset",
    "env",
    "experiment",
    "gym",
    "indicator",
    "label",
    "model",
    "plot",
    "portfolio",
    "ray",
    "signal",
    "stats",
    "transform",
    "utils",
]