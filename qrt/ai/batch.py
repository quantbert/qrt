"""Stable-key, resumable batch inference."""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import pandas as pd
import pyarrow as pa
from pydantic import BaseModel

from qrt.ai.client import Client
from qrt.ai.storage import RunStore


def _records(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, pd.DataFrame):
        return data.to_dict(orient="records")
    if isinstance(data, pa.Table):
        return data.to_pylist()
    return [item.model_dump() if isinstance(item, BaseModel) else dict(item) for item in data]


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


@dataclass
class BatchRun:
    run_id: str
    results: pd.DataFrame
    failures: pd.DataFrame
    usage: pd.DataFrame
    provenance: dict[str, Any]
    _resume: Any

    def resume(self) -> BatchRun:
        """Retry only rows that did not produce a durable success."""
        return self._resume()


def extract(
    data: Any,
    *,
    key: str,
    input: str,
    client: Client,
    model: str,
    output: type[BaseModel],
    store: RunStore | None = None,
    run_id: str | None = None,
    provider_options: dict[str, Any] | None = None,
) -> BatchRun:
    """Extract typed values while preserving stable row identity."""
    rows = _records(data)
    keys = [str(row[key]) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("batch keys must be unique")
    store = store or RunStore()
    schema_hash = _hash(output.model_json_schema())
    configuration = {"model": model, "schema_hash": schema_hash, "provider_options": provider_options or {}}
    configuration_hash = _hash(configuration)
    run_id = run_id or uuid.uuid4().hex
    successes: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    usage_rows: list[dict[str, Any]] = []
    for row in rows:
        row_key = str(row[key])
        cache_key = _hash(
            {"input": row[input], "key": row_key, "configuration": configuration_hash, "contract": "qrt.ai.batch.v1"}
        )
        cached = store.cache_get(cache_key)
        if cached is not None:
            successes.append({"key": row_key, "value": cached["value"], "cache_hit": True})
            usage_rows.append({"key": row_key, "cache_hit": True})
            continue
        try:
            result = client.extract(
                model=model,
                input=str(row[input]),
                output=output,
                provider_options=provider_options,
            )
        except Exception as exc:
            failures.append({"key": row_key, "error_type": type(exc).__name__, "message": str(exc)})
            continue
        value = result.structured.model_dump(mode="json")
        successes.append({"key": row_key, "value": value, "cache_hit": False})
        usage_rows.append(
            {"key": row_key, "cache_hit": False, **(result.usage.model_dump() if result.usage else {})}
        )
        store.cache_put(cache_key, {"value": value, "provenance": result.provenance.model_dump(mode="json")})
    status = "completed" if not failures else "partial"
    manifest = {
        "keys": keys,
        "successful_keys": [item["key"] for item in successes],
        "failed_keys": [item["key"] for item in failures],
        "configuration": configuration,
    }
    store.save_manifest(run_id, "extract", configuration_hash, status, manifest)
    store.write_artifact(run_id, "results", successes)
    store.write_artifact(run_id, "failures", failures)
    store.write_artifact(run_id, "usage", usage_rows)

    def resume() -> BatchRun:
        failed = set(item["key"] for item in failures)
        return extract(
            [row for row in rows if str(row[key]) in failed],
            key=key,
            input=input,
            client=client,
            model=model,
            output=output,
            store=store,
            run_id=run_id,
            provider_options=provider_options,
        )

    return BatchRun(
        run_id=run_id,
        results=pd.DataFrame(successes).set_index("key") if successes else pd.DataFrame(index=pd.Index([], name="key")),
        failures=pd.DataFrame(failures).set_index("key") if failures else pd.DataFrame(index=pd.Index([], name="key")),
        usage=pd.DataFrame(usage_rows).set_index("key") if usage_rows else pd.DataFrame(index=pd.Index([], name="key")),
        provenance={"configuration_hash": configuration_hash, "schema_hash": schema_hash},
        _resume=resume,
    )