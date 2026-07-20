"""General-purpose helper functions.

Add new concerns (config loading, caching, retry helpers, ...) as
additional modules in this package as they land.
"""

import os
import random
import shutil
from pathlib import Path

import numpy as np
from joblib import Memory
from platformdirs import user_cache_dir
from qrt.env import load as load_env
from rich.console import Console

__all__ = [
    "cache_dir",
    "clear_cache",
    "console",
    "load_env",
    "log",
    "memory",
    "set_seed",
]

#: Shared rich console for pretty CLI/notebook output (progress, tables, ...).
console = Console()


def cache_dir(name: str = "") -> Path:
    """Return (creating if needed) qrt's OS-standard user cache directory.

    Resolved via :mod:`platformdirs`, e.g. ``~/.cache/qrt`` on Linux,
    ``~/Library/Caches/qrt`` on macOS. Used as the default location for
    downloaded/cached data (see ``q.data.sources``) so caches don't depend
    on the current working directory.

    Args:
        name: Optional subdirectory under the qrt cache dir (e.g. ``"joblib"``).
    """
    path = Path(user_cache_dir("qrt"))
    if name:
        path = path / name
    path.mkdir(parents=True, exist_ok=True)
    return path


#: Disk-backed memoization for expensive, pure functions, e.g.:
#:     @q.utils.memory.cache
#:     def slow_feature(df): ...
memory = Memory(location=cache_dir("joblib"), verbose=0)


def clear_cache(name: str = "") -> None:
    """Delete qrt's cached files, e.g. for a clean re-fetch or freeing disk space.

    Safe to call anytime: caches (downloaded OHLC/trades parquet, joblib
    memoization, ...) are rebuilt lazily on next use.

    Args:
        name: Optional subdirectory to clear (e.g. ``"data"``, ``"joblib"``).
            If omitted, clears everything under :func:`cache_dir`.
    """
    if name in ("", "joblib"):
        memory.clear(warn=False)
    target = cache_dir(name)
    shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True, exist_ok=True)


def log(values):
  """Return the element-wise natural logarithm of scalar or array-like values.

  This delegates to :func:`numpy.log`, preserving pandas Series and
  DataFrame labels. For simple returns ``r``, use ``log(1 + r)`` to obtain
  log returns.
  """
  return np.log(values)


def set_seed(seed: int = 42, strict_determinism: bool = False) -> None:
    """Set random seed for reproducibility across various libraries. If none is given, default is 42.

    Args:
        seed: Random seed to use.
        strict_determinism: If True, also forces deterministic cuDNN
            kernels, disables cuDNN auto-tuning, and enables
            `torch.use_deterministic_algorithms(True)` for stronger
            reproducibility guarantees, at the cost of speed and possible
            errors (see Caveats). Defaults to False.

    Caveats:
        - Enabling `torch.use_deterministic_algorithms(True)` can raise a
          `RuntimeError` if an op has no deterministic implementation. The
          `CUBLAS_WORKSPACE_CONFIG` environment variable is set to
          `:4096:8` automatically (unless already set) as required by CUDA.
        - `torch.backends.cudnn.deterministic = True` and
          `torch.backends.cudnn.benchmark = False` can noticeably slow down
          training since cuDNN can no longer auto-tune kernels.
        - Determinism is not guaranteed across different PyTorch versions,
          hardware, or number of threads/devices.
    """
    # Imported lazily: torch adds ~0.7s to import time, unnecessary weight
    # for the many qrt uses that never touch it.
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    if strict_determinism:
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        torch.use_deterministic_algorithms(True)
