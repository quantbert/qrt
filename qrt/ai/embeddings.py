"""Hosted and local embedding contracts."""

from __future__ import annotations

from importlib.metadata import version
from typing import Any

from pydantic import Field

from qrt._optional import missing_optional_dependency
from qrt.ai.types import AIModel, ModelRef, OpenAICompatibleProvider, ProviderConfig, Usage


class EmbeddingResult(AIModel):
    model: ModelRef
    resolved_model: str
    vectors: tuple[tuple[float, ...], ...]
    dimension: int
    normalized: bool | None = None
    usage: Usage | None = None
    backend: str
    backend_version: str | None = None
    input_hashes: tuple[str, ...] = Field(default_factory=tuple)


def hosted_embed(
    inputs: list[str],
    *,
    model: ModelRef,
    provider: ProviderConfig,
    dimensions: int | None = None,
    provider_options: dict[str, Any] | None = None,
) -> EmbeddingResult:
    """Embed text through LiteLLM without exposing its response types."""
    try:
        import litellm
    except ModuleNotFoundError as exc:
        if exc.name == "litellm":
            missing_optional_dependency(namespace="q.ai.embed", extra="ai", dependency="litellm")
        raise
    kwargs: dict[str, Any] = {
        "model": model.name,
        "input": inputs,
        "dimensions": dimensions,
        **(provider_options or {}),
    }
    if isinstance(provider, OpenAICompatibleProvider):
        kwargs["api_base"] = provider.base_url
    if provider.api_key is not None:
        kwargs["api_key"] = provider.api_key.get_secret_value()
    response = litellm.embedding(**kwargs)
    data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
    ordered = sorted(data["data"], key=lambda item: item.get("index", 0))
    vectors = tuple(tuple(float(value) for value in item["embedding"]) for item in ordered)
    usage_data = data.get("usage") or {}
    usage = Usage(
        input_tokens=usage_data.get("prompt_tokens"),
        total_tokens=usage_data.get("total_tokens"),
    ) if usage_data else None
    import hashlib

    return EmbeddingResult(
        model=model,
        resolved_model=str(data.get("model") or model.name),
        vectors=vectors,
        dimension=len(vectors[0]) if vectors else 0,
        usage=usage,
        backend="litellm",
        backend_version=version("litellm"),
        input_hashes=tuple(hashlib.sha256(text.encode()).hexdigest() for text in inputs),
    )


class SentenceTransformerEmbedding:
    """Lazy local sentence-transformer embedding backend."""

    def __init__(self, model: str = "BAAI/bge-small-en-v1.5", *, normalize: bool = True) -> None:
        self.model = model
        self.normalize = normalize
        self._encoder = None

    def __call__(self, texts: list[str]) -> list[list[float]]:
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ModuleNotFoundError as exc:
                if exc.name == "sentence_transformers":
                    missing_optional_dependency(
                        namespace="q.ai.embeddings", extra="ai-local", dependency="sentence-transformers"
                    )
                raise
            self._encoder = SentenceTransformer(self.model)
        vectors = self._encoder.encode(texts, normalize_embeddings=self.normalize)
        return vectors.tolist()