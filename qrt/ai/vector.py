"""LanceDB-backed embedded vector indexes."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any

from pydantic import Field

from qrt._optional import missing_optional_dependency
from qrt.ai.types import AIModel


class VectorMatch(AIModel):
    key: str
    text: str
    distance: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class VectorIndex:
    """A persistent LanceDB vector index with point-in-time filtering."""

    def __init__(
        self,
        name: str,
        *,
        path: str | Path,
        embedding: Callable[[list[str]], Sequence[Sequence[float]]],
    ) -> None:
        try:
            import lancedb
        except ModuleNotFoundError as exc:
            if exc.name == "lancedb":
                missing_optional_dependency(namespace="q.ai.vector", extra="ai", dependency="lancedb")
            raise
        self.name = name
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self._db = lancedb.connect(self.path)
        self._embedding = embedding
        names = set(self._db.list_tables().tables)
        self._table = self._db.open_table(name) if name in names else None

    def add(
        self,
        records: Iterable[dict[str, Any]],
        *,
        text: str = "text",
        key: str = "id",
        metadata: Sequence[str] = (),
        mode: str = "append",
    ) -> None:
        rows = list(records)
        if not rows:
            return
        missing_times = [index for index, row in enumerate(rows) if not row.get("published_at") or not row.get("ingested_at")]
        if missing_times:
            raise ValueError("every vector record requires published_at and ingested_at")
        vectors = self._embedding([str(row[text]) for row in rows])
        payload = []
        for row, vector in zip(rows, vectors, strict=True):
            extra = {field: row.get(field) for field in metadata}
            payload.append(
                {
                    "key": str(row[key]),
                    "text": str(row[text]),
                    "vector": [float(value) for value in vector],
                    "published_at": str(row["published_at"]),
                    "ingested_at": str(row["ingested_at"]),
                    "metadata_json": json.dumps(extra, sort_keys=True, default=str),
                }
            )
        if self._table is None:
            self._table = self._db.create_table(self.name, payload)
        else:
            self._table.add(payload, mode=mode)

    def search(
        self,
        query: str,
        *,
        as_of: str | None = None,
        where: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[VectorMatch]:
        if self._table is None:
            return []
        vector = list(self._embedding([query])[0])
        builder = self._table.search(vector, vector_column_name="vector").limit(limit)
        filters: list[str] = []
        if as_of is not None:
            escaped = as_of.replace("'", "''")
            filters.append(f"published_at <= '{escaped}'")
        if filters:
            builder = builder.where(" AND ".join(filters), prefilter=True)
        matches = []
        for row in builder.to_list():
            metadata = json.loads(row.get("metadata_json") or "{}")
            if where and any(metadata.get(field) != value for field, value in where.items()):
                continue
            matches.append(
                VectorMatch(
                    key=row["key"], text=row["text"], distance=row.get("_distance"), metadata=metadata
                )
            )
        return matches[:limit]

    def delete(self, key: str) -> None:
        if self._table is not None:
            self._table.delete(f"key = '{key.replace(chr(39), chr(39) * 2)}'")

    def close(self) -> None:
        self._table = None
        self._db = None


def open(
    name: str,
    *,
    path: str | Path = ".qrt/ai/vectors",
    embedding: Callable[[list[str]], Sequence[Sequence[float]]],
    backend: str = "lancedb",
) -> VectorIndex:
    """Open a persistent vector index."""
    if backend != "lancedb":
        raise ValueError(f"unsupported vector backend {backend!r}")
    return VectorIndex(name, path=path, embedding=embedding)


def attach_to_duckdb(connection, path: str | Path, *, alias: str = "qrt_vectors") -> None:
    """Install/load DuckDB's Lance extension and attach a LanceDB directory."""
    connection.execute("INSTALL lance")
    connection.execute("LOAD lance")
    safe_path = str(Path(path).resolve()).replace("'", "''")
    safe_alias = "".join(character for character in alias if character.isalnum() or character == "_")
    if not safe_alias or safe_alias != alias:
        raise ValueError("alias must contain only letters, numbers, and underscores")
    connection.execute(f"ATTACH '{safe_path}' AS {safe_alias} (TYPE LANCE)")