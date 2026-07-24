"""Installed integration status and diagnostics."""

from __future__ import annotations

import importlib.util
from importlib.metadata import PackageNotFoundError, version

from qrt.ai.types import AIModel


class IntegrationStatus(AIModel):
    name: str
    status: str
    installed: bool
    version: str | None = None
    capabilities: tuple[str, ...] = ()


_INTEGRATIONS = {
    "litellm": ("preferred", ("generation", "embedding")),
    "lancedb": ("preferred", ("vector", "hybrid_search")),
    "pydantic_ai": ("preferred", ("agents",)),
    "llama_index": ("preferred", ("rag", "chunking")),
    "docling": ("preferred", ("document",)),
    "sentence_transformers": ("preferred", ("local_embedding", "reranking")),
    "transformers": ("supported", ("local_generation",)),
    "outlines": ("supported", ("constrained_decoding",)),
}


def report() -> tuple[IntegrationStatus, ...]:
    rows = []
    for package, (status, capabilities) in _INTEGRATIONS.items():
        installed = importlib.util.find_spec(package) is not None
        try:
            package_version = version(package.replace("_", "-")) if installed else None
        except PackageNotFoundError:
            package_version = None
        rows.append(IntegrationStatus(name=package, status=status, installed=installed, version=package_version, capabilities=capabilities))
    return tuple(rows)


def doctor() -> dict[str, object]:
    integrations = report()
    return {"ok": all(item.installed for item in integrations if item.status == "preferred"), "integrations": [item.model_dump() for item in integrations]}