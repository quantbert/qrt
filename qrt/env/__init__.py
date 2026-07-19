"""Environment variable and ``.env`` file helpers.

Loading is always explicit: importing :mod:`qrt.env` does not modify the
process environment. Runtime inspection helpers describe the operating
system, storage, and compute accelerators available to qrt.
"""

from __future__ import annotations

import os
import platform
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import dotenv_values, load_dotenv

__all__ = [
    "AcceleratorInfo",
    "DiskInfo",
    "EnvironmentInfo",
    "EnvironmentRequirementError",
    "OSInfo",
    "accelerators",
    "device",
    "disk",
    "get",
    "info",
    "load",
    "operating_system",
    "report",
    "require",
    "values",
]


@dataclass(frozen=True)
class OSInfo:
    """Operating-system details for the current runtime."""

    name: str
    release: str
    version: str
    machine: str


@dataclass(frozen=True)
class DiskInfo:
    """Filesystem capacity containing a requested path, in bytes."""

    path: Path
    total: int
    used: int
    free: int


@dataclass(frozen=True)
class AcceleratorInfo:
    """A compute accelerator available to the installed PyTorch runtime."""

    index: int
    backend: str
    vendor: str
    name: str
    memory_total: int | None = None


@dataclass(frozen=True)
class EnvironmentInfo:
    """Snapshot of the environment in which qrt is running."""

    operating_system: OSInfo
    disk: DiskInfo
    accelerators: tuple[AcceleratorInfo, ...]
    device: str

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the snapshot."""
        result = asdict(self)
        result["disk"]["path"] = str(self.disk.path)
        return result


class EnvironmentRequirementError(RuntimeError):
    """Raised when the runtime does not satisfy environment requirements."""

    def __init__(self, failures: list[str]) -> None:
        self.failures = tuple(failures)
        details = "\n".join(f"- {failure}" for failure in failures)
        super().__init__(f"Environment requirements not satisfied:\n{details}")


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


def require(name: str | Path) -> str | EnvironmentInfo:
    """Require one variable or validate a runtime requirements file.

    Dispatch is based on the argument:

    - A string ending in ``.yml`` or ``.yaml`` validates that requirements file
      and returns an :class:`EnvironmentInfo` snapshot.
    - Any :class:`~pathlib.Path` validates that requirements file, regardless
      of its suffix.
    - Any other string is looked up in the process environment and its value
      is returned.

    Raises:
        KeyError: If a requested variable is not set.
        ValueError: If a requirements file has an invalid schema.
        EnvironmentRequirementError: If runtime requirements are not met.
    """
    if isinstance(name, Path) or name.lower().endswith((".yml", ".yaml")):
        return _require_file(Path(name))
    try:
        return os.environ[name]
    except KeyError:
        raise KeyError(f"Required environment variable is not set: {name}") from None


_SIZE_PATTERN = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*([kmgt]?i?b)\s*$", re.I)
_SIZE_MULTIPLIERS = {
    "b": 1,
    "kb": 1000,
    "kib": 1024,
    "mb": 1000**2,
    "mib": 1024**2,
    "gb": 1000**3,
    "gib": 1024**3,
    "tb": 1000**4,
    "tib": 1024**4,
}


def _parse_size(value: object, field: str) -> int:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    if isinstance(value, str) and (match := _SIZE_PATTERN.fullmatch(value)):
        return int(float(match.group(1)) * _SIZE_MULTIPLIERS[match.group(2).lower()])
    raise ValueError(f"{field} must be non-negative bytes or a size such as '10 GiB'")


def _choices(value: object, field: str) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return tuple(value)
    raise ValueError(f"{field} must be a string or list of strings")


def _check_keys(values: dict[str, Any], allowed: set[str], field: str) -> None:
    unknown = values.keys() - allowed
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ValueError(f"Unknown {field} requirement(s): {names}")


def _require_file(path: Path) -> EnvironmentInfo:
    requirement_path = path.expanduser().resolve()
    with requirement_path.open(encoding="utf-8") as file:
        requirements = yaml.safe_load(file) or {}
    if not isinstance(requirements, dict):
        raise ValueError("Environment requirements must be a YAML mapping")
    _check_keys(
        requirements,
        {"os", "machine", "disk", "accelerator", "env"},
        "top-level",
    )

    disk_requirement = requirements.get("disk", {})
    if not isinstance(disk_requirement, dict):
        raise ValueError("disk must be a mapping")
    _check_keys(disk_requirement, {"path", "free"}, "disk")
    disk_path = Path(disk_requirement.get("path", ".")).expanduser()
    if not disk_path.is_absolute():
        disk_path = requirement_path.parent / disk_path

    snapshot = info(disk_path)
    failures: list[str] = []

    if "os" in requirements:
        allowed = _choices(requirements["os"], "os")
        if snapshot.operating_system.name.casefold() not in {
            value.casefold() for value in allowed
        }:
            failures.append(
                f"OS is {snapshot.operating_system.name!r}; expected one of {allowed!r}"
            )

    if "machine" in requirements:
        allowed = _choices(requirements["machine"], "machine")
        if snapshot.operating_system.machine.casefold() not in {
            value.casefold() for value in allowed
        }:
            failures.append(
                f"machine is {snapshot.operating_system.machine!r}; "
                f"expected one of {allowed!r}"
            )

    if "free" in disk_requirement:
        minimum_free = _parse_size(disk_requirement["free"], "disk.free")
        if snapshot.disk.free < minimum_free:
            failures.append(
                f"disk at {snapshot.disk.path} has {_format_bytes(snapshot.disk.free)} "
                f"free; requires {_format_bytes(minimum_free)}"
            )

    accelerator_requirement = requirements.get("accelerator")
    if accelerator_requirement is not None:
        if not isinstance(accelerator_requirement, dict):
            raise ValueError("accelerator must be a mapping")
        _check_keys(
            accelerator_requirement,
            {"backends", "vendors", "count", "memory"},
            "accelerator",
        )
        backends = _choices(
            accelerator_requirement.get(
                "backends", [item.backend for item in snapshot.accelerators]
            ),
            "accelerator.backends",
        )
        vendors = _choices(
            accelerator_requirement.get(
                "vendors", [item.vendor for item in snapshot.accelerators]
            ),
            "accelerator.vendors",
        )
        count = accelerator_requirement.get("count", 1)
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise ValueError("accelerator.count must be a non-negative integer")
        minimum_memory = _parse_size(
            accelerator_requirement.get("memory", 0), "accelerator.memory"
        )
        matching = [
            item
            for item in snapshot.accelerators
            if item.backend.casefold() in {value.casefold() for value in backends}
            and item.vendor.casefold() in {value.casefold() for value in vendors}
            and (item.memory_total or 0) >= minimum_memory
        ]
        if len(matching) < count:
            failures.append(
                f"found {len(matching)} matching accelerator(s); requires {count} "
                f"with backend {backends!r}, vendor {vendors!r}, and at least "
                f"{_format_bytes(minimum_memory)} memory"
            )

    env_names = requirements.get("env", [])
    if not isinstance(env_names, list) or not all(
        isinstance(item, str) for item in env_names
    ):
        raise ValueError("env must be a list of variable names")
    missing = [name for name in env_names if not os.environ.get(name)]
    if missing:
        failures.append(f"required environment variable(s) not set: {', '.join(missing)}")

    if failures:
        raise EnvironmentRequirementError(failures)
    return snapshot


def operating_system() -> OSInfo:
    """Return details about the operating system running qrt."""
    return OSInfo(
        name=platform.system(),
        release=platform.release(),
        version=platform.version(),
        machine=platform.machine(),
    )


def disk(path: str | Path = ".") -> DiskInfo:
    """Return capacity for the filesystem containing ``path``.

    Args:
        path: Path whose filesystem should be inspected. If it does not exist,
            its nearest existing parent is used to query filesystem capacity.
    """
    resolved = Path(path).expanduser().resolve()
    probe = resolved
    while not probe.exists():
        probe = probe.parent
    usage = shutil.disk_usage(probe)
    return DiskInfo(
        path=resolved,
        total=usage.total,
        used=usage.used,
        free=usage.free,
    )


def accelerators() -> tuple[AcceleratorInfo, ...]:
    """Return compute accelerators usable by the installed PyTorch runtime.

    PyTorch exposes AMD ROCm devices through its ``torch.cuda`` API, so
    ``torch.version.hip`` is used to distinguish AMD from NVIDIA devices.
    """
    import torch

    detected: list[AcceleratorInfo] = []
    if torch.cuda.is_available():
        is_rocm = torch.version.hip is not None
        for index in range(torch.cuda.device_count()):
            properties = torch.cuda.get_device_properties(index)
            detected.append(
                AcceleratorInfo(
                    index=index,
                    backend="rocm" if is_rocm else "cuda",
                    vendor="AMD" if is_rocm else "NVIDIA",
                    name=torch.cuda.get_device_name(index),
                    memory_total=properties.total_memory,
                )
            )

    if torch.backends.mps.is_available():
        detected.append(
            AcceleratorInfo(
                index=0,
                backend="mps",
                vendor="Apple",
                name="Apple Silicon GPU",
            )
        )

    xpu = getattr(torch, "xpu", None)
    if xpu is not None and xpu.is_available():
        for index in range(xpu.device_count()):
            properties = xpu.get_device_properties(index)
            detected.append(
                AcceleratorInfo(
                    index=index,
                    backend="xpu",
                    vendor="Intel",
                    name=xpu.get_device_name(index),
                    memory_total=getattr(properties, "total_memory", None),
                )
            )

    return tuple(detected)


def device() -> str:
    """Return the preferred PyTorch device for the current environment."""
    available = accelerators()
    if not available:
        return "cpu"
    if available[0].backend == "rocm":
        return "cuda"
    return available[0].backend


def info(path: str | Path = ".") -> EnvironmentInfo:
    """Return a snapshot of qrt's current runtime environment."""
    available = accelerators()
    preferred = "cpu"
    if available:
        preferred = "cuda" if available[0].backend == "rocm" else available[0].backend
    return EnvironmentInfo(
        operating_system=operating_system(),
        disk=disk(path),
        accelerators=available,
        device=preferred,
    )


def _format_bytes(value: int | None) -> str:
    if value is None:
        return "unknown"
    size = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(size) < 1024 or unit == "TiB":
            return f"{size:.1f} {unit}"
        size /= 1024
    raise AssertionError("unreachable")


def report(path: str | Path = ".") -> EnvironmentInfo:
    """Print a Rich environment summary and return its structured snapshot."""
    from rich.console import Console
    from rich.table import Table

    snapshot = info(path)
    table = Table(title="qrt environment", show_header=False)
    table.add_column("Property", style="bold")
    table.add_column("Value")
    system = snapshot.operating_system
    table.add_row("OS", f"{system.name} {system.release} ({system.machine})")
    table.add_row(
        "Disk",
        f"{_format_bytes(snapshot.disk.free)} free of "
        f"{_format_bytes(snapshot.disk.total)} at {snapshot.disk.path}",
    )
    if snapshot.accelerators:
        for accelerator in snapshot.accelerators:
            table.add_row(
                "Accelerator",
                f"{accelerator.vendor} {accelerator.name} "
                f"({accelerator.backend}, {_format_bytes(accelerator.memory_total)})",
            )
    else:
        table.add_row("Accelerator", "None detected")
    table.add_row("Preferred device", snapshot.device)
    Console().print(table)
    return snapshot