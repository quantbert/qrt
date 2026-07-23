"""Lazy access to Ray's distributed computing APIs.

Use Ray through the QRT namespace without paying its import cost until an
attribute is accessed::

    q.ray.init()
    q.ray.data.read_parquet(...)
    q.ray.tune.run(...)
"""

from __future__ import annotations

import importlib
from typing import Any


_SUBMODULES = {"data", "rllib", "serve", "train", "tune"}


def __getattr__(name: str) -> Any:
    if name in _SUBMODULES:
        value = importlib.import_module(f"ray.{name}")
    else:
        value = getattr(importlib.import_module("ray"), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    ray = importlib.import_module("ray")
    return sorted(set(globals()) | set(dir(ray)) | _SUBMODULES)


__all__ = ["data", "rllib", "serve", "train", "tune"]