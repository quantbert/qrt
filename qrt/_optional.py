"""Shared optional-dependency errors for QRT integrations."""

from __future__ import annotations

from collections.abc import Callable
from typing import NoReturn


class OptionalDependencyError(ImportError):
    """An optional QRT integration is not installed."""


def missing_optional_dependency(
    *,
    namespace: str,
    extra: str,
    dependency: str | None = None,
) -> NoReturn:
    """Raise the standard actionable error for a missing optional dependency."""
    package = dependency or extra
    raise OptionalDependencyError(
        f"{namespace} requires the '{extra}' extra ({package}); "
        f"install it with `uv add 'pyqrt[{extra}]'`"
    ) from None


def require_optional(
    loader: Callable[[], object],
    *,
    namespace: str,
    extra: str,
    dependency: str | None = None,
) -> object:
    """Run an integration loader and normalize a direct missing import."""
    try:
        return loader()
    except ModuleNotFoundError as exc:
        expected = dependency or extra
        if exc.name == expected or (exc.name and exc.name.startswith(f"{expected}.")):
            missing_optional_dependency(
                namespace=namespace,
                extra=extra,
                dependency=dependency,
            )
        raise