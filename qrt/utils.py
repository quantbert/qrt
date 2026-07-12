"""General-purpose helper functions."""

import os
import random

import numpy as np
import torch

__all__ = ["log", "set_seed"]


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
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    if strict_determinism:
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        torch.use_deterministic_algorithms(True)
