"""Named, versioned feature definitions and materialization.

``q.feature`` owns the lifecycle of model inputs: metadata, point-in-time
computation, feature sets, and persistence. Market measurements live in
``q.indicator``; fitted training transformations live in ``q.preprocess``.
"""

from qrt.feature import ops
from qrt.feature._core import Feature, FeatureSet, compute, materialize

__all__ = ["Feature", "FeatureSet", "compute", "materialize", "ops"]
