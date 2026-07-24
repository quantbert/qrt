"""Durable DuckDB catalogs and Parquet artifacts for QRT AI runs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq


class RunStore:
    """Transactional run metadata with portable columnar artifacts."""

    def __init__(self, path: str | Path = ".qrt/ai/runs") -> None:
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.database_path = self.path / "runs.duckdb"
        self.connection = duckdb.connect(str(self.database_path))
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_runs (
                run_id VARCHAR PRIMARY KEY,
                operation VARCHAR NOT NULL,
                configuration_hash VARCHAR NOT NULL,
                status VARCHAR NOT NULL,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                manifest JSON NOT NULL
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_cache (
                cache_key VARCHAR PRIMARY KEY,
                value JSON NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )

    def save_manifest(self, run_id: str, operation: str, configuration_hash: str, status: str, manifest: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc)
        self.connection.execute(
            """
            INSERT INTO ai_runs VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (run_id) DO UPDATE SET
                status = excluded.status,
                updated_at = excluded.updated_at,
                manifest = excluded.manifest
            """,
            [run_id, operation, configuration_hash, status, now, now, json.dumps(manifest, default=str)],
        )

    def load_manifest(self, run_id: str) -> dict[str, Any] | None:
        row = self.connection.execute("SELECT manifest FROM ai_runs WHERE run_id = ?", [run_id]).fetchone()
        return json.loads(row[0]) if row else None

    def cache_get(self, key: str) -> dict[str, Any] | None:
        row = self.connection.execute("SELECT value FROM ai_cache WHERE cache_key = ?", [key]).fetchone()
        return json.loads(row[0]) if row else None

    def cache_put(self, key: str, value: dict[str, Any]) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO ai_cache VALUES (?, ?, ?)",
            [key, json.dumps(value, default=str), datetime.now(timezone.utc)],
        )

    def write_artifact(self, run_id: str, name: str, rows: list[dict[str, Any]]) -> Path:
        destination = self.path / run_id / f"{name}.parquet"
        destination.parent.mkdir(parents=True, exist_ok=True)
        normalized = [
            {
                key: json.dumps(value, sort_keys=True, default=str)
                if isinstance(value, (dict, list, tuple))
                else value
                for key, value in row.items()
            }
            for row in rows
        ]
        table = pa.Table.from_pylist(normalized) if normalized else pa.table({"key": pa.array([], type=pa.string())})
        pq.write_table(table, destination)
        return destination

    def close(self) -> None:
        self.connection.close()