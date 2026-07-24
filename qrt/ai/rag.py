"""Point-in-time retrieval-augmented generation workflows."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import Field

from qrt._optional import missing_optional_dependency
from qrt.ai.client import Client
from qrt.ai.types import AIModel, GenerationResult, UserMessage
from qrt.ai.vector import VectorIndex, VectorMatch


class SourceDocument(AIModel):
    source_id: str
    text: str
    published_at: datetime
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    effective_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeBase(AIModel):
    name: str
    chunk_count: int
    chunking: str
    index_path: str
    model_config = {"arbitrary_types_allowed": True, "frozen": True}
    index: Any = Field(exclude=True, repr=False)


class RAGAnswer(AIModel):
    result: GenerationResult[Any]
    sources: tuple[VectorMatch, ...]

    @property
    def text(self) -> str:
        return self.result.text


def _split(text: str, *, chunk_size: int, chunk_overlap: int) -> list[str]:
    try:
        from llama_index.core.node_parser import SentenceSplitter
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("llama_index"):
            missing_optional_dependency(namespace="q.ai.rag", extra="ai", dependency="llama-index-core")
        raise
    return SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap).split_text(text)


def index(
    documents: Iterable[SourceDocument],
    *,
    store: VectorIndex,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> KnowledgeBase:
    """Chunk and index source documents with stable content-derived IDs."""
    rows = []
    for document in documents:
        source_hash = hashlib.sha256(document.text.encode()).hexdigest()
        for position, chunk in enumerate(_split(document.text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)):
            rows.append(
                {
                    "id": f"{document.source_id}:{source_hash[:16]}:{position}",
                    "text": chunk,
                    "published_at": document.published_at.isoformat(),
                    "ingested_at": document.ingested_at.isoformat(),
                    "source_id": document.source_id,
                    **document.metadata,
                }
            )
    metadata = sorted({key for row in rows for key in row} - {"id", "text", "published_at", "ingested_at"})
    store.add(rows, metadata=metadata)
    return KnowledgeBase(
        name=store.name,
        chunk_count=len(rows),
        chunking=f"llama-index-sentence:{chunk_size}:{chunk_overlap}",
        index_path=str(store.path),
        index=store,
    )


def ask(
    question: str,
    *,
    knowledge: KnowledgeBase,
    client: Client,
    model: str,
    as_of: str,
    where: dict[str, Any] | None = None,
    limit: int = 8,
) -> RAGAnswer:
    """Retrieve point-in-time context and generate a source-grounded answer."""
    sources = tuple(knowledge.index.search(question, as_of=as_of, where=where, limit=limit))
    context = "\n\n".join(f"[{source.key}] {source.text}" for source in sources)
    prompt = (
        "Answer using only the supplied sources. Cite source keys in brackets.\n\n"
        f"Sources:\n{context}\n\nQuestion: {question}"
    )
    result = client.generate(model=model, messages=[UserMessage(prompt)])
    return RAGAnswer(result=result, sources=sources)