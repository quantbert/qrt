"""PyTorch model helpers.

Wraps `torchinfo <https://github.com/TylerYep/torchinfo>`_ for inspecting
models: a Keras-style layer-by-layer summary with output shapes, parameter
counts, and estimated memory usage -- handy for sanity-checking an
architecture before training.

    q.model.torch.summary(model, input_size=...)

Examples:
    >>> q.model.torch.summary(mymodel, input_size=(32, 30, 10))  # (batch, seq, features)
    >>> q.model.torch.summary(mymodel, input_data=batch)         # or pass a real batch
"""

from __future__ import annotations

from torchinfo import ModelStatistics, summary

__all__ = ["ModelStatistics", "summary"]
