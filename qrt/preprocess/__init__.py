"""Fitted transformations applied at the model-training boundary.

Preprocessors must fit on training data and retain that fitted state for
validation, testing, and inference. They are not globally materialized market
features.
"""

from qrt.preprocess import encode, impute, outlier, reduction, scale, selection

__all__ = ["encode", "impute", "outlier", "reduction", "scale", "selection"]