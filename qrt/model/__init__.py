"""ML model utilities: helpers for building, inspecting, and training models.

Structured as a namespace of submodules:

    q.model.torch       -- PyTorch helpers (model summaries via torchinfo, etc.)
    q.model.selection   -- leakage-aware CV splitters (walk-forward, purged
                           K-fold, embargo), named after scikit-learn's
                           ``model_selection``

To add your own framework family or model-lifecycle helper, create
``qrt/model/<name>.py`` (or a ``qrt/model/<name>/`` subpackage), then
register it in the imports and ``__all__`` below. It becomes available as
``q.model.<name>``.
"""

from qrt.model import selection, torch

__all__ = ["selection", "torch"]
