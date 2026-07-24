"""Private backend contracts and deterministic test implementation."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Iterator
from dataclasses import dataclass
from typing import Any, Protocol

from qrt.ai.types import CapabilityFact, Message, ModelRef, OutputBlock, TextDelta, TextOutput, Usage


@dataclass(frozen=True)
class BackendRequest:
    model: ModelRef
    messages: tuple[Message, ...]
    temperature: float | None
    top_p: float | None
    max_output_tokens: int | None
    stop: tuple[str, ...]
    seed: int | None
    timeout: float | None
    output_schema: dict[str, Any] | None
    provider_options: dict[str, Any]
    include_raw: bool


@dataclass(frozen=True)
class BackendResponse:
    resolved_model: str
    content: tuple[OutputBlock, ...]
    usage: Usage | None = None
    finish_reason: str | None = None
    request_id: str | None = None
    raw: Any | None = None
    integration: str = "unknown"
    integration_version: str | None = None
    structured_mechanism: str | None = None


class Backend(Protocol):
    def generate(self, request: BackendRequest) -> BackendResponse: ...

    async def agenerate(self, request: BackendRequest) -> BackendResponse: ...

    def stream(self, request: BackendRequest) -> Iterator[TextDelta]: ...

    async def astream(self, request: BackendRequest) -> AsyncIterator[TextDelta]: ...

    def capabilities(self, model: ModelRef) -> dict[str, CapabilityFact]: ...


class MemoryBackend:
    """Private deterministic backend used by contract tests and examples."""

    def __init__(self, responder: str | Callable[[BackendRequest], str]) -> None:
        self._responder = responder

    def _text(self, request: BackendRequest) -> str:
        if callable(self._responder):
            return self._responder(request)
        return self._responder

    def generate(self, request: BackendRequest) -> BackendResponse:
        text = self._text(request)
        return BackendResponse(
            resolved_model=str(request.model),
            content=(TextOutput(text=text),),
            usage=Usage(output_tokens=len(text.split())),
            finish_reason="stop",
            integration="memory",
            structured_mechanism="test" if request.output_schema else None,
        )

    async def agenerate(self, request: BackendRequest) -> BackendResponse:
        return self.generate(request)

    def stream(self, request: BackendRequest) -> Iterator[TextDelta]:
        for token in self._text(request).split(" "):
            yield TextDelta(text=f"{token} ")

    async def astream(self, request: BackendRequest) -> AsyncIterator[TextDelta]:
        for event in self.stream(request):
            yield event

    def capabilities(self, model: ModelRef) -> dict[str, CapabilityFact]:
        return {
            "generation": CapabilityFact(status="supported", source="declared"),
            "structured_output": CapabilityFact(status="supported", source="declared"),
        }