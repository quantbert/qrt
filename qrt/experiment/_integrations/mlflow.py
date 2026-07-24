"""MLflow tracking integration behind QRT experiment contracts."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from qrt._optional import missing_optional_dependency


class MLflowBackend:
    """Track QRT experiments through an explicit MLflow client."""

    def __init__(
        self,
        *,
        experiment: str,
        tracking_uri: str | None = None,
        registry_uri: str | None = None,
    ) -> None:
        resolved_tracking_uri = tracking_uri or os.environ.get("MLFLOW_TRACKING_URI")
        if resolved_tracking_uri is None:
            raise ValueError(
                "MLflowTracker requires tracking_uri or MLFLOW_TRACKING_URI; "
                "use an HTTP server or database-backed tracking store"
            )
        try:
            from mlflow.tracking import MlflowClient
        except ModuleNotFoundError as exc:
            if exc.name and exc.name.startswith("mlflow"):
                missing_optional_dependency(
                    namespace="q.experiment.MLflowTracker",
                    extra="experiment",
                    dependency="mlflow-skinny",
                )
            raise
        self.client = MlflowClient(
            tracking_uri=resolved_tracking_uri,
            registry_uri=registry_uri,
        )
        existing = self.client.get_experiment_by_name(experiment)
        self.experiment_id = (
            existing.experiment_id
            if existing is not None
            else self.client.create_experiment(experiment)
        )

    def start_run(self, *, name: str, tags: dict[str, str]) -> str:
        return self.client.create_run(
            self.experiment_id,
            run_name=name,
            tags=tags,
        ).info.run_id

    def end_run(self, run_id: str, *, status: str) -> None:
        self.client.set_terminated(run_id, status=status)

    def log_params(self, run_id: str, params: dict[str, Any]) -> None:
        for key, value in params.items():
            self.client.log_param(run_id, key, _string(value))

    def log_metrics(self, run_id: str, metrics: dict[str, float], *, step: int | None) -> None:
        for key, value in metrics.items():
            self.client.log_metric(run_id, key, float(value), step=step)

    def set_tags(self, run_id: str, tags: dict[str, str]) -> None:
        for key, value in tags.items():
            self.client.set_tag(run_id, key, value)

    def log_artifact(self, run_id: str, path: Path, *, artifact_path: str | None) -> str:
        self.client.log_artifact(run_id, str(path), artifact_path=artifact_path)
        return f"mlflow://{run_id}/{artifact_path + '/' if artifact_path else ''}{path.name}"

    def log_record(self, run_id: str, kind: str, name: str, record: dict[str, Any]) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / f"{name}.json"
            path.write_text(json.dumps(record, indent=2, sort_keys=True, default=str))
            self.log_artifact(run_id, path, artifact_path=kind)


def _string(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))