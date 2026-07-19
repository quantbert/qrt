"""Environment variable and ``.env`` file helpers.

Loading is always explicit: importing :mod:`qrt.env` does not modify the
process environment.
"""

import os
from pathlib import Path
from typing import Any

from dotenv import dotenv_values, load_dotenv

__all__ = ["get", "load", "require", "values"]


def load(
    path: str | Path | None = None,
    *,
    override: bool = False,
    **kwargs: Any,
) -> bool:
    """Load variables from a ``.env`` file into the process environment.

    Args:
        path: File to load. If omitted, python-dotenv searches upward for
            a ``.env`` file.
        override: Whether loaded values replace variables already present in
            the process environment.
        **kwargs: Additional options passed to :func:`dotenv.load_dotenv`.

    Returns:
        ``True`` when at least one variable was loaded, otherwise ``False``.
    """
    return load_dotenv(dotenv_path=path, override=override, **kwargs)


def values(path: str | Path | None = None, **kwargs: Any) -> dict[str, str | None]:
    """Read a ``.env`` file without modifying the process environment.

    Args:
        path: File to read. If omitted, python-dotenv searches upward for
            a ``.env`` file.
        **kwargs: Additional options passed to :func:`dotenv.dotenv_values`.

    Returns:
        Parsed variable names and values.
    """
    return dict(dotenv_values(dotenv_path=path, **kwargs))


def get(name: str, default: str | None = None) -> str | None:
    """Return an environment variable, or ``default`` when it is unset."""
    return os.getenv(name, default)


def require(name: str) -> str:
    """Return a required environment variable.

    Raises:
        KeyError: If the variable is not set.
    """
    try:
        return os.environ[name]
    except KeyError:
        raise KeyError(f"Required environment variable is not set: {name}") from None