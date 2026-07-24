"""QRT's curated generative-AI workbench."""

from __future__ import annotations

from qrt.ai.client import AsyncStream, Client, Stream
from qrt.ai.errors import *
from qrt.ai.types import *
from qrt.ai import agents, batch, document, embeddings, evals, finetune, integrations, local, prompts, rag, serve, storage, tokenize, tools, vector
from qrt.ai.agents import Agent, AgentLimits
from qrt.ai.tools import tool


_default_client: Client | None = None


def default_client() -> Client:
    """Return the lazily constructed environment-derived client."""
    global _default_client
    if _default_client is None:
        _default_client = Client()
    return _default_client


def generate(**kwargs):
    """Generate a normalized result using the default client."""
    return default_client().generate(**kwargs)


async def agenerate(**kwargs):
    """Asynchronously generate a normalized result using the default client."""
    return await default_client().agenerate(**kwargs)


def extract(**kwargs):
    """Generate and validate a Pydantic object using the default client."""
    return default_client().extract(**kwargs)


def embed(inputs, *, model, **kwargs):
    """Embed inputs using a configured provider on the default client."""
    model_ref, _ = default_client().resolve_model(model)
    provider = default_client().providers[model_ref.provider]
    return embeddings.hosted_embed(list(inputs), model=model_ref, provider=provider, **kwargs)


__all__ = [
    "AgentLimits",
    "AssistantMessage",
    "CapabilityFact",
    "Client",
    "GenerationResult",
    "HostedProvider",
    "ImageBytesInput",
    "ImagePathInput",
    "ImageURLInput",
    "MediaPolicy",
    "ModelDeployment",
    "ModelRef",
    "OpenAICompatibleProvider",
    "RedactionPolicy",
    "RetryPolicy",
    "SystemMessage",
    "TextDelta",
    "TextInput",
    "TextOutput",
    "ToolCallOutput",
    "Usage",
    "UserMessage",
    "agenerate",
    "default_client",
    "extract",
    "embed",
    "embeddings",
    "generate",
    "Agent",
    "AgentLimits",
    "agents",
    "batch",
    "document",
    "evals",
    "finetune",
    "integrations",
    "local",
    "prompts",
    "rag",
    "serve",
    "storage",
    "tokenize",
    "tool",
    "tools",
    "vector",
]