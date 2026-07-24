"""DuckDB metadata and local-file artifacts for experiment tracking."""

from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb


class LocalBackend:
    """Persist experiment runs locally without an external service."""

    def __init__(self, path: str | Path = ".qrt/experiments") -> None:
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.artifact_root = self.path / "artifacts"
        self.artifact_root.mkdir(exist_ok=True)
        self.connection = duckdb.connect(str(self.path / "experiments.duckdb"))
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS experiment_runs (
                run_id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                status VARCHAR NOT NULL,
                started_at TIMESTAMPTZ NOT NULL,
                ended_at TIMESTAMPTZ
            );
            CREATE TABLE IF NOT EXISTS experiment_values (
                run_id VARCHAR NOT NULL,
                kind VARCHAR NOT NULL,
                key VARCHAR NOT NULL,
                value JSON NOT NULL,
                step BIGINT,
                recorded_at TIMESTAMPTZ NOT NULL
            );
            CREATE TABLE IF NOT EXISTS experiment_artifacts (
                run_id VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                path VARCHAR NOT NULL,
                recorded_at TIMESTAMPTZ NOT NULL
            );
            """
        )

    def start_run(self, *, name: str, tags: dict[str, str]) -> str:
        run_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc)
        self.connection.execute(
            "INSERT INTO experiment_runs VALUES (?, ?, 'RUNNING', ?, NULL)",
            [run_id, name, now],
        )
        self.set_tags(run_id, tags)
        return run_id

    def end_run(self, run_id: str, *, status: str) -> None:
        self.connection.execute(
            "UPDATE experiment_runs SET status = ?, ended_at = ? WHERE run_id = ?",
            [status, datetime.now(timezone.utc), run_id],
        )

    def _values(
        self,
        run_id: str,
        kind: str,
        values: dict[str, Any],
        *,
        step: int | None = None,
    ) -> None:
        if not values:
            return
        now = datetime.now(timezone.utc)
        self.connection.executemany(
            "INSERT INTO experiment_values VALUES (?, ?, ?, ?, ?, ?)",
            [
                [run_id, kind, key, json.dumps(value, default=str), step, now]
                for key, value in values.items()
            ],
        )

    def log_params(self, run_id: str, params: dict[str, Any]) -> None:
        self._values(run_id, "param", params)

    def log_metrics(self, run_id: str, metrics: dict[str, float], *, step: int | None) -> None:
        self._values(run_id, "metric", metrics, step=step)

    def set_tags(self, run_id: str, tags: dict[str, str]) -> None:
        self._values(run_id, "tag", tags)

    def log_artifact(self, run_id: str, path: Path, *, artifact_path: str | None) -> str:
        if not path.is_file():
            raise FileNotFoundError(f"artifact must be a file: {path}")
        destination = self.artifact_root / run_id
        if artifact_path:
            destination /= artifact_path
        destination.mkdir(parents=True, exist_ok=True)
        copied = destination / path.name
        shutil.copy2(path, copied)
        self.connection.execute(
            "INSERT INTO experiment_artifacts VALUES (?, ?, ?, ?)",
            [run_id, path.name, str(copied), datetime.now(timezone.utc)],
        )
        return str(copied)

    def log_record(self, run_id: str, kind: str, name: str, record: dict[str, Any]) -> None:
        self._values(run_id, kind, {name: record})

    def run(self, run_id: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT run_id, name, status, started_at, ended_at FROM experiment_runs WHERE run_id = ?",
            [run_id],
        ).fetchone()
        if row is None:
            return None
        values = self.connection.execute(
            "SELECT kind, key, value, step FROM experiment_values WHERE run_id = ? ORDER BY recorded_at",
            [run_id],
        ).fetchall()
        return {
            "run_id": row[0],
            "name": row[1],
            "status": row[2],
            "started_at": row[3],
            "ended_at": row[4],
            "values": [
                {"kind": kind, "key": key, "value": json.loads(value), "step": step}
                for kind, key, value, step in values
            ],
        }

    def close(self) -> None:
        self.connection.close()