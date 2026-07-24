"""Backend-neutral experiment run lifecycle and logging API."""

from __future__ import annotations

import contextvars
from pathlib import Path
from types import TracebackType
from typing import Any

from qrt.experiment._backend import ExperimentBackend
from qrt.experiment._integrations.mlflow import MLflowBackend
from qrt.experiment.local import LocalBackend


_active_run: contextvars.ContextVar[Run | None] = contextvars.ContextVar(
    "qrt_experiment_run",
    default=None,
)


class Run:
    """A context-managed experiment run with backend-neutral logging."""

    def __init__(self, backend: ExperimentBackend, *, name: str, tags: dict[str, str]) -> None:
        self.backend = backend
        self.name = name
        self.tags = dict(tags)
        self.run_id: str | None = None
        self._token: contextvars.Token[Run | None] | None = None
        self.status = "PENDING"

    def __enter__(self) -> Run:
        if self.run_id is not None:
            raise RuntimeError("an experiment run cannot be entered twice")
        self.run_id = self.backend.start_run(name=self.name, tags=self.tags)
        self.status = "RUNNING"
        self._token = _active_run.set(self)
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exception, traceback
        status = "FAILED" if exception_type is not None else "FINISHED"
        try:
            self.backend.end_run(self._require_id(), status=status)
            self.status = status
        finally:
            if self._token is not None:
                _active_run.reset(self._token)

    def _require_id(self) -> str:
        if self.run_id is None:
            raise RuntimeError("logging requires an active experiment run context")
        return self.run_id

    def log_params(self, params: dict[str, Any] | None = None, **values: Any) -> None:
        self.backend.log_params(self._require_id(), {**(params or {}), **values})

    def log_metrics(
        self,
        metrics: dict[str, float] | None = None,
        *,
        step: int | None = None,
        **values: float,
    ) -> None:
        self.backend.log_metrics(self._require_id(), {**(metrics or {}), **values}, step=step)

    def set_tags(self, tags: dict[str, str] | None = None, **values: str) -> None:
        self.backend.set_tags(self._require_id(), {**(tags or {}), **values})

    def log_artifact(self, path: str | Path, *, artifact_path: str | None = None) -> str:
        return self.backend.log_artifact(
            self._require_id(),
            Path(path),
            artifact_path=artifact_path,
        )

    def log_dataset(
        self,
        name: str,
        *,
        fingerprint: str,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.backend.log_record(
            self._require_id(),
            "datasets",
            name,
            {"fingerprint": fingerprint, "source": source, "metadata": metadata or {}},
        )

    def log_record(self, kind: str, name: str, record: dict[str, Any]) -> None:
        """Log a backend-neutral structured record as metadata or an artifact."""
        self.backend.log_record(self._require_id(), kind, name, record)

    def log_model(
        self,
        name: str,
        *,
        artifact: str | Path | None = None,
        flavor: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        record = {"flavor": flavor, "metadata": metadata or {}}
        if artifact is not None:
            record["artifact_uri"] = self.log_artifact(artifact, artifact_path=f"models/{name}")
        self.backend.log_record(self._require_id(), "models", name, record)


class LocalTracker:
    """Create runs in QRT's local DuckDB and artifact store."""

    def __init__(self, path: str | Path = ".qrt/experiments") -> None:
        self.backend = LocalBackend(path)

    def run(self, name: str, *, tags: dict[str, str] | None = None) -> Run:
        return Run(self.backend, name=name, tags=tags or {})

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        return self.backend.run(run_id)

    def close(self) -> None:
        self.backend.close()


class MLflowTracker:
    """Create runs in a configured MLflow tracking server or file store."""

    def __init__(
        self,
        *,
        experiment: str,
        tracking_uri: str | None = None,
        registry_uri: str | None = None,
    ) -> None:
        self.backend = MLflowBackend(
            experiment=experiment,
            tracking_uri=tracking_uri,
            registry_uri=registry_uri,
        )

    def run(self, name: str, *, tags: dict[str, str] | None = None) -> Run:
        return Run(self.backend, name=name, tags=tags or {})

    @property
    def backend_client(self):
        return self.backend.client


Tracker = LocalTracker | MLflowTracker
_default_tracker: LocalTracker | None = None


def active_run() -> Run | None:
    """Return the run active in the current context, if any."""
    return _active_run.get()


def default_tracker() -> LocalTracker:
    """Return the lazily constructed process-local tracker."""
    global _default_tracker
    if _default_tracker is None:
        _default_tracker = LocalTracker()
    return _default_tracker


def run(
    name: str,
    *,
    tracker: Tracker | None = None,
    tags: dict[str, str] | None = None,
) -> Run:
    """Create a local run unless an explicit tracker is supplied."""
    return (tracker or default_tracker()).run(name, tags=tags)