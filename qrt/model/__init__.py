"""ML model utilities: helpers for building, inspecting, and training models.

Two kinds of submodules live here:

- Framework-agnostic helpers -- no import of a specific ML framework, work
  on plain arrays/indices/callables. Flat siblings at this level, e.g.:

    q.model.selection   -- leakage-aware CV splitters (walk-forward, purged
                           K-fold, embargo), named after scikit-learn's
                           ``model_selection``

- Framework-specific adapters -- thin wrappers around one library's actual
  model objects/training API. Each framework gets its own submodule, which
  may grow into its own subpackage as it picks up multiple concerns (e.g.
  training loops, checkpointing, dataloaders alongside model summaries) --
  same convention as ``qrt.feature``/``qrt.data``:

    q.model.torch       -- PyTorch helpers (model summaries via torchinfo
                           today; training/checkpointing/dataloaders as
                           they land, per the roadmap)

Don't add a generic dispatching helper (e.g. a framework-agnostic `train()`
that inspects the model type and picks a backend) -- signatures don't
unify across frameworks, and it's the same registry/ABC ceremony already
rejected elsewhere in this codebase (see ``qrt.data.sources``). Add a new
framework submodule only once it's actually used, not speculatively.

To add your own framework family or model-lifecycle helper, create
``qrt/model/<name>.py`` (or a ``qrt/model/<name>/`` subpackage), then
register it in the imports and ``__all__`` below. It becomes available as
``q.model.<name>``.
"""

from typing import TYPE_CHECKING

from qrt.model import selection

if TYPE_CHECKING:
    from qrt.model import torch


def __getattr__(name: str) -> object:
    # Lazily import the PyTorch-backed submodule: an eager import here
    # would pull in torch (~0.7s import) on every `import qrt`. Uses
    # importlib because `from qrt.model import torch` would re-trigger
    # this __getattr__ and recurse.
    if name == "torch":
        import importlib

        return importlib.import_module("qrt.model.torch")
    raise AttributeError(f"module 'qrt.model' has no attribute {name!r}")


__all__ = ["selection", "torch"]
