from datetime import datetime, timezone

import pytest

import qrt as q
from qrt.ai._backend import MemoryBackend


pytest.importorskip("lancedb")
pytest.importorskip("llama_index")


def embed(texts):
    return [[float("risk" in text.lower()), float(len(text) % 7), 1.0] for text in texts]


def test_lancedb_vector_search_requires_time_and_enforces_as_of(tmp_path):
    index = q.ai.vector.open("filings", path=tmp_path, embedding=embed)
    try:
        index.add([{"id": "bad", "text": "missing timestamps"}])
    except ValueError as exc:
        assert "published_at and ingested_at" in str(exc)
    else:
        raise AssertionError("timestamps must be required")

    index.add(
        [
            {"id": "old", "text": "liquidity risk", "published_at": "2025-01-01", "ingested_at": "2025-01-02", "symbol": "ACME"},
            {"id": "future", "text": "new refinancing risk", "published_at": "2026-01-01", "ingested_at": "2026-01-02", "symbol": "ACME"},
        ],
        metadata=["symbol"],
    )

    matches = index.search("risk", as_of="2025-06-01", where={"symbol": "ACME"})
    assert [match.key for match in matches] == ["old"]


def test_rag_indexes_with_llamaindex_and_answers_with_sources(tmp_path):
    vector_index = q.ai.vector.open("knowledge", path=tmp_path, embedding=embed)
    document = q.ai.rag.SourceDocument(
        source_id="filing-1",
        text="ACME disclosed refinancing risk and reduced available liquidity.",
        published_at=datetime(2025, 3, 1, tzinfo=timezone.utc),
    )
    knowledge = q.ai.rag.index([document], store=vector_index, chunk_size=20, chunk_overlap=2)
    client = q.ai.Client(
        providers={"test": q.ai.HostedProvider()},
        _backends={"test": MemoryBackend("Liquidity weakened [filing-1].")},
    )

    answer = q.ai.rag.ask(
        "What changed?", knowledge=knowledge, client=client, model="test/model", as_of="2025-03-31"
    )

    assert answer.sources
    assert answer.text.startswith("Liquidity weakened")
    assert knowledge.chunking.startswith("llama-index-sentence")