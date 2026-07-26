"""Typed local Lean CLI orchestration.

The adapter launches the standalone ``lean`` command without changing the
caller's working directory. LEAN remains responsible for execution and native
artifacts; QRT adds lifecycle handling and report integration.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from threading import Lock, Thread
from typing import Any, TextIO
from uuid import uuid4

from qrt.bt._report import BacktestReport, _latest_result, report as create_report


Parameter = str | int | float | bool
Command = str | Sequence[str]


class LeanError(RuntimeError):
    """Base class for Lean adapter failures."""


class LeanDependencyError(LeanError):
    """Raised when the Lean CLI executable cannot be located."""


class LeanValidationError(LeanError):
    """Raised when a workspace or command input is invalid."""


class LeanArtifactError(LeanError):
    """Raised when a successful backtest did not produce a result artifact."""


class LeanRunState(StrEnum):
    """Lifecycle state for a Lean CLI process."""

    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


@dataclass(frozen=True, slots=True)
class LeanRunSpecification:
    """Immutable, JSON-serializable Lean command specification."""

    workspace: Path
    executable: Path
    arguments: tuple[str, ...]

    @property
    def command(self) -> tuple[str, ...]:
        """Return the complete argv passed to the operating system."""
        return (str(self.executable), *self.arguments)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "workspace": str(self.workspace),
            "executable": str(self.executable),
            "arguments": list(self.arguments),
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        """Serialize this specification to JSON."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


@dataclass(frozen=True, slots=True)
class LeanCommandResult:
    """Terminal result of a general Lean CLI command."""

    specification: LeanRunSpecification
    state: LeanRunState
    returncode: int
    stdout: str
    stderr: str
    started_at: datetime
    ended_at: datetime

    @property
    def succeeded(self) -> bool:
        return self.state is LeanRunState.SUCCEEDED


@dataclass(frozen=True, slots=True)
class LeanBacktestResult(LeanCommandResult):
    """Completed Lean backtest with preserved native artifact paths."""

    algorithm: Path
    output_directory: Path
    result_path: Path | None
    artifacts: tuple[Path, ...]
    parameters: tuple[tuple[str, Parameter], ...]

    def report(
        self,
        destination: str | Path,
        *,
        title: str | None = None,
        description: str = "",
    ) -> BacktestReport:
        """Create a native QRT report from this run's exact result JSON."""
        if self.result_path is None:
            raise LeanArtifactError("This backtest has no LEAN result JSON")
        return create_report(
            self.result_path,
            title=title,
            description=description,
            output=destination,
        )


class LeanCommandError(LeanError):
    """Raised when a Lean CLI command exits unsuccessfully."""

    def __init__(self, result: LeanCommandResult) -> None:
        self.result = result
        detail = result.stderr.strip() or result.stdout.strip()
        suffix = f": {detail[-500:]}" if detail else ""
        super().__init__(f"Lean command failed with exit code {result.returncode}{suffix}")


class LeanTimeoutError(LeanCommandError):
    """Raised after a command exceeds its wait timeout and is terminated."""


def _resolve_executable(executable: str | Path | None) -> Path:
    if executable is not None:
        requested = Path(executable).expanduser()
        if requested.parent != Path("."):
            resolved = requested.resolve()
            if resolved.is_file():
                return resolved
        found = shutil.which(str(requested))
    else:
        found = shutil.which("lean")
        if found is None:
            sibling = Path(sys.executable).resolve().parent / "lean"
            found = str(sibling) if sibling.is_file() else None
    if found is None:
        raise LeanDependencyError(
            "Lean CLI was not found. Install the 'lean' package or pass executable='/path/to/lean'."
        )
    return Path(found).resolve()


def _workspace_path(workspace: str | Path, *, create: bool = False) -> Path:
    path = Path(workspace).expanduser().resolve()
    if create:
        path.mkdir(parents=True, exist_ok=True)
    if not path.is_dir():
        raise LeanValidationError(f"Lean workspace does not exist: {path}")
    return path


def _command_arguments(command: Command) -> tuple[str, ...]:
    arguments = tuple(shlex.split(command) if isinstance(command, str) else (str(value) for value in command))
    if not arguments:
        raise LeanValidationError("Lean command cannot be empty")
    if Path(arguments[0]).name == "lean":
        raise LeanValidationError("Pass only the arguments after 'lean', for example 'data download ...'")
    return arguments


def _read_stream(stream: TextIO | None, target: list[str], lock: Lock) -> None:
    if stream is None:
        return
    for line in stream:
        with lock:
            target.append(line)
    stream.close()


class LeanRun:
    """A running Lean CLI process."""

    def __init__(self, specification: LeanRunSpecification) -> None:
        self.specification = specification
        self.started_at = datetime.now(timezone.utc)
        self._state = LeanRunState.RUNNING
        self._lock = Lock()
        self._stdout: list[str] = []
        self._stderr: list[str] = []
        try:
            self._process = subprocess.Popen(
                specification.command,
                cwd=specification.workspace,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except OSError as error:
            raise LeanDependencyError(f"Unable to launch Lean CLI: {error}") from error
        self._threads = (
            Thread(target=_read_stream, args=(self._process.stdout, self._stdout, self._lock), daemon=True),
            Thread(target=_read_stream, args=(self._process.stderr, self._stderr, self._lock), daemon=True),
        )
        for thread in self._threads:
            thread.start()

    @property
    def state(self) -> LeanRunState:
        """Return the current lifecycle state."""
        returncode = self._process.poll()
        if self._state is LeanRunState.RUNNING and returncode is not None:
            self._state = LeanRunState.SUCCEEDED if returncode == 0 else LeanRunState.FAILED
        return self._state

    @property
    def stdout(self) -> str:
        """Return stdout captured so far."""
        with self._lock:
            return "".join(self._stdout)

    @property
    def stderr(self) -> str:
        """Return stderr captured so far."""
        with self._lock:
            return "".join(self._stderr)

    def _terminal_result(self, returncode: int) -> LeanCommandResult:
        return LeanCommandResult(
            specification=self.specification,
            state=self._state,
            returncode=returncode,
            stdout=self.stdout,
            stderr=self.stderr,
            started_at=self.started_at,
            ended_at=datetime.now(timezone.utc),
        )

    def wait(self, timeout: float | None = None, *, check: bool = True) -> LeanCommandResult:
        """Wait for completion, optionally terminating after ``timeout`` seconds."""
        timed_out = False
        try:
            returncode = self._process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            self._state = LeanRunState.TIMED_OUT
            self._process.terminate()
            try:
                returncode = self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                returncode = self._process.wait()
        for thread in self._threads:
            thread.join()
        if not timed_out and self._state is LeanRunState.RUNNING:
            self._state = LeanRunState.SUCCEEDED if returncode == 0 else LeanRunState.FAILED
        result = self._terminal_result(returncode)
        if check and result.state is not LeanRunState.SUCCEEDED:
            error = LeanTimeoutError if timed_out else LeanCommandError
            raise error(result)
        return result

    def cancel(self, *, grace_period: float = 5.0) -> LeanCommandResult:
        """Terminate this command and return its cancelled result."""
        if self._process.poll() is None:
            self._state = LeanRunState.CANCELLED
            self._process.terminate()
            try:
                self._process.wait(timeout=grace_period)
            except subprocess.TimeoutExpired:
                self._process.kill()
        returncode = self._process.wait()
        for thread in self._threads:
            thread.join()
        return self._terminal_result(returncode)


class LeanBacktestRun(LeanRun):
    """A running Lean backtest with deterministic artifact ownership."""

    def __init__(
        self,
        specification: LeanRunSpecification,
        *,
        algorithm: Path,
        output_directory: Path,
        parameters: tuple[tuple[str, Parameter], ...],
    ) -> None:
        self.algorithm = algorithm
        self.output_directory = output_directory
        self.parameters = parameters
        super().__init__(specification)

    def _backtest_result(self, result: LeanCommandResult) -> LeanBacktestResult:
        result_path: Path | None = None
        if result.succeeded:
            try:
                _, result_path = _latest_result(self.output_directory)
            except FileNotFoundError as error:
                raise LeanArtifactError(
                    f"Lean exited successfully but produced no result JSON in {self.output_directory}"
                ) from error
        artifacts = tuple(sorted(path for path in self.output_directory.rglob("*") if path.is_file()))
        return LeanBacktestResult(
            specification=result.specification,
            state=result.state,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            started_at=result.started_at,
            ended_at=result.ended_at,
            algorithm=self.algorithm,
            output_directory=self.output_directory,
            result_path=result_path,
            artifacts=artifacts,
            parameters=self.parameters,
        )

    def wait(self, timeout: float | None = None, *, check: bool = True) -> LeanBacktestResult:
        """Wait for LEAN and resolve this run's exact native artifacts."""
        result = super().wait(timeout=timeout, check=False)
        backtest_result = self._backtest_result(result)
        if check and not backtest_result.succeeded:
            error = LeanTimeoutError if result.state is LeanRunState.TIMED_OUT else LeanCommandError
            raise error(backtest_result)
        return backtest_result

    def cancel(self, *, grace_period: float = 5.0) -> LeanBacktestResult:
        """Terminate this backtest and retain any artifacts already written."""
        result = super().cancel(grace_period=grace_period)
        return self._backtest_result(result)


def run(
    command: Command,
    *,
    workspace: str | Path = ".",
    executable: str | Path | None = None,
) -> LeanRun:
    """Launch whatever follows the ``lean`` command inside ``workspace``.

    Examples:
        ``q.bt.lean.run("config get engine-image", workspace="lean/project")``
    """
    workspace_path = _workspace_path(workspace)
    specification = LeanRunSpecification(
        workspace=workspace_path,
        executable=_resolve_executable(executable),
        arguments=_command_arguments(command),
    )
    return LeanRun(specification)


def init(
    *,
    workspace: str | Path,
    organization: str | None = None,
    language: str | None = None,
    executable: str | Path | None = None,
    timeout: float | None = None,
) -> LeanCommandResult:
    """Create a workspace and run ``lean init`` in it synchronously."""
    workspace_path = _workspace_path(workspace, create=True)
    arguments = ["init"]
    if organization:
        arguments.extend(("--organization", organization))
    if language:
        normalized = language.lower()
        if normalized not in {"python", "csharp"}:
            raise LeanValidationError("language must be 'python' or 'csharp'")
        arguments.extend(("--language", normalized))
    return run(arguments, workspace=workspace_path, executable=executable).wait(timeout=timeout)


def _validate_backtest_workspace(workspace: Path, algorithm: Path) -> None:
    missing = [
        path
        for path in (workspace / "lean.json", workspace / "config.json", workspace / "data", algorithm)
        if not path.exists()
    ]
    if missing:
        rendered = ", ".join(str(path) for path in missing)
        raise LeanValidationError(f"Lean workspace is not ready; missing: {rendered}")
    try:
        configuration = json.loads((workspace / "config.json").read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise LeanValidationError(f"Unable to read project config.json: {error}") from error
    if not isinstance(configuration, dict):
        raise LeanValidationError("Project config.json must contain a JSON object")
    language = str(configuration.get("algorithm-language", "")).lower()
    if language == "python" and algorithm.suffix.lower() != ".py":
        raise LeanValidationError("Python LEAN projects require a .py algorithm")
    if language in {"csharp", "c#"} and algorithm.suffix.lower() != ".cs":
        raise LeanValidationError("C# LEAN projects require a .cs algorithm")


def _parameter_value(value: Parameter) -> str:
    return str(value).lower() if isinstance(value, bool) else str(value)


def _prepare_output_root(root: Path) -> None:
    try:
        root.mkdir(parents=True, exist_ok=True)
    except PermissionError as error:
        raise LeanValidationError(
            f"Backtest output root is not writable: {root}. "
            "Fix its ownership or pass output_root= to a user-owned directory."
        ) from error
    if not os.access(root, os.W_OK | os.X_OK):
        raise LeanValidationError(
            f"Backtest output root is not writable: {root}. "
            "Fix its ownership or pass output_root= to a user-owned directory."
        )


def _validate_docker_access() -> None:
    docker = shutil.which("docker")
    if docker is None:
        raise LeanDependencyError("Docker CLI was not found; local LEAN backtests require Docker.")
    try:
        check = subprocess.run(
            (docker, "info", "--format", "{{.ServerVersion}}"),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise LeanDependencyError(f"Unable to query Docker: {error}") from error
    if check.returncode:
        detail = check.stderr.strip() or check.stdout.strip()
        raise LeanValidationError(
            "Docker is not accessible to this Python/Jupyter user. Configure rootless Docker "
            "or Docker group access, then restart the notebook server/kernel. Do not pass a "
            f"sudo password to q.bt.lean. Docker said: {detail[-500:]}"
        )


def backtest(
    *,
    workspace: str | Path,
    algorithm: str | Path,
    parameters: Mapping[str, Parameter] | None = None,
    update_image: bool = False,
    image: str | None = None,
    executable: str | Path | None = None,
    output_root: str | Path | None = None,
) -> LeanBacktestRun:
    """Launch a local LEAN backtest and return its asynchronous run handle."""
    workspace_path = _workspace_path(workspace)
    algorithm_path = Path(algorithm).expanduser()
    if not algorithm_path.is_absolute():
        algorithm_path = workspace_path / algorithm_path
    algorithm_path = algorithm_path.resolve()
    _validate_backtest_workspace(workspace_path, algorithm_path)
    executable_path = _resolve_executable(executable)

    if output_root:
        root = Path(output_root).expanduser()
        if not root.is_absolute():
            root = workspace_path / root
        root = root.resolve()
    else:
        root = workspace_path / "backtests"
    _prepare_output_root(root)
    _validate_docker_access()
    run_id = f"{datetime.now(timezone.utc):%Y-%m-%d_%H-%M-%S}_{uuid4().hex[:8]}"
    output_directory = (root / run_id).resolve()
    output_directory.mkdir()

    normalized_parameters = tuple((str(key), value) for key, value in (parameters or {}).items())
    arguments = ["backtest", str(algorithm_path), "--output", str(output_directory)]
    arguments.append("--update" if update_image else "--no-update")
    if image:
        arguments.extend(("--image", image))
    for key, value in normalized_parameters:
        arguments.extend(("--parameter", key, _parameter_value(value)))

    specification = LeanRunSpecification(
        workspace=workspace_path,
        executable=executable_path,
        arguments=tuple(arguments),
    )
    return LeanBacktestRun(
        specification,
        algorithm=algorithm_path,
        output_directory=output_directory,
        parameters=normalized_parameters,
    )


__all__ = [
    "LeanArtifactError",
    "LeanBacktestResult",
    "LeanBacktestRun",
    "LeanCommandError",
    "LeanCommandResult",
    "LeanDependencyError",
    "LeanError",
    "LeanRun",
    "LeanRunSpecification",
    "LeanRunState",
    "LeanTimeoutError",
    "LeanValidationError",
    "backtest",
    "init",
    "run",
]
