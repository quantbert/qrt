"""Docling-backed document ingestion into stable QRT source records."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from qrt.ai.rag import SourceDocument


def load(path: str | Path, *, published_at: datetime, source_id: str | None = None) -> SourceDocument:
    """Convert a document with Docling while preserving its source identity."""
    from docling.document_converter import DocumentConverter

    source = Path(path).resolve()
    result = DocumentConverter().convert(source)
    return SourceDocument(
        source_id=source_id or str(source),
        text=result.document.export_to_markdown(),
        published_at=published_at,
        ingested_at=datetime.now(timezone.utc),
        metadata={"path": str(source), "parser": "docling"},
    )