"""Errors raised by the QRT generative-AI workbench."""

from __future__ import annotations


class AIError(Exception):
    """Base class for QRT AI errors."""


class ModelResolutionError(AIError):
    """A logical model cannot be resolved to a configured provider."""


class CapabilityError(AIError):
    """A requested operation is unsupported by the selected backend."""


class StructuredOutputError(AIError):
    """Base class for structured-output failures."""


class StructuredOutputParseError(StructuredOutputError):
    """Generated structured output is not valid JSON."""


class StructuredOutputValidationError(StructuredOutputError):
    """Generated structured output does not satisfy the requested schema."""


class SchemaNotSupportedError(StructuredOutputError):
    """The selected backend cannot represent the requested schema."""


class StreamClosedError(AIError):
    """A final stream result was requested before the stream completed."""