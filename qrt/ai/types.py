"""Shared messages, results, capabilities, usage, and provenance types."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


class AIModel(BaseModel):
    """Immutable base model for public QRT AI contracts."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class ModelRef(AIModel):
    """A provider-qualified model identity."""

    provider: str
    name: str

    def __str__(self) -> str:
        return f"{self.provider}/{self.name}"


class ModelDeployment(AIModel):
    """A stable logical alias for a deployed model."""

    model: ModelRef
    revision: str | None = None
    base_model: str | None = None
    adapter: str | None = None


class TextInput(AIModel):
    type: Literal["text"] = "text"
    text: str


class ImageURLInput(AIModel):
    type: Literal["image_url"] = "image_url"
    url: str


class ImageBytesInput(AIModel):
    type: Literal["image_bytes"] = "image_bytes"
    data: bytes = Field(repr=False)
    media_type: str


class ImagePathInput(AIModel):
    type: Literal["image_path"] = "image_path"
    path: str
    media_type: str | None = None


class AudioInput(AIModel):
    type: Literal["audio"] = "audio"
    data: bytes = Field(repr=False)
    media_type: str


class FileInput(AIModel):
    type: Literal["file"] = "file"
    path: str
    media_type: str | None = None


class ToolResultInput(AIModel):
    type: Literal["tool_result"] = "tool_result"
    call_id: str
    value: Any


InputBlock = (
    TextInput
    | ImageURLInput
    | ImageBytesInput
    | ImagePathInput
    | AudioInput
    | FileInput
    | ToolResultInput
)


class Message(AIModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: tuple[InputBlock, ...]

    @field_validator("content", mode="before")
    @classmethod
    def _coerce_content(cls, value: Any) -> Any:
        if isinstance(value, str):
            return (TextInput(text=value),)
        return tuple(value)


class SystemMessage(Message):
    role: Literal["system"] = "system"

    def __init__(self, content: str | tuple[InputBlock, ...], **data: Any) -> None:
        super().__init__(content=content, **data)


class UserMessage(Message):
    role: Literal["user"] = "user"

    def __init__(self, content: str | tuple[InputBlock, ...], **data: Any) -> None:
        super().__init__(content=content, **data)


class AssistantMessage(Message):
    role: Literal["assistant"] = "assistant"

    def __init__(self, content: str | tuple[InputBlock, ...], **data: Any) -> None:
        super().__init__(content=content, **data)


class TextOutput(AIModel):
    type: Literal["text"] = "text"
    text: str


class RefusalOutput(AIModel):
    type: Literal["refusal"] = "refusal"
    reason: str


class ToolCallOutput(AIModel):
    type: Literal["tool_call"] = "tool_call"
    call_id: str
    name: str
    arguments: dict[str, Any]


class CitationOutput(AIModel):
    type: Literal["citation"] = "citation"
    source_id: str
    start: int | None = None
    end: int | None = None


class ReasoningSummaryOutput(AIModel):
    type: Literal["reasoning_summary"] = "reasoning_summary"
    text: str


class UnknownOutput(AIModel):
    type: Literal["unknown"] = "unknown"
    provider_type: str
    data: dict[str, Any]


OutputBlock = (
    TextOutput
    | RefusalOutput
    | ToolCallOutput
    | CitationOutput
    | ReasoningSummaryOutput
    | UnknownOutput
)


class Usage(AIModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_tokens: int | None = None
    reasoning_tokens: int | None = None
    total_tokens: int | None = None
    request_cost: float | None = None
    latency_seconds: float | None = None
    time_to_first_token_seconds: float | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class CapabilityFact(AIModel):
    status: Literal["supported", "unsupported", "unknown"]
    source: Literal["declared", "observed", "backend"]
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InferenceProvenance(AIModel):
    logical_model: ModelRef
    resolved_model: str
    provider: str
    deployment_revision: str | None = None
    base_model: str | None = None
    adapter: str | None = None
    prompt_hash: str
    schema_hash: str | None = None
    options_hash: str
    provider_options_hash: str | None = None
    structured_mechanism: str | None = None
    qrt_version: str
    integration: str
    integration_version: str | None = None
    experiment_run_id: str | None = None
    started_at: datetime
    completed_at: datetime


FinishReason = Literal["stop", "length", "tool_call", "refusal", "cancelled", "error", "unknown"]
T = TypeVar("T")


class GenerationResult(AIModel, Generic[T]):
    logical_model: ModelRef
    resolved_model: str
    content: tuple[OutputBlock, ...]
    structured: T | None = None
    usage: Usage | None = None
    finish_reason: FinishReason | None = None
    provider_finish_reason: str | None = None
    request_id: str | None = None
    provenance: InferenceProvenance
    raw: Any | None = Field(default=None, exclude=True, repr=False)

    @property
    def text(self) -> str:
        """Concatenate canonical text output blocks."""
        return "".join(block.text for block in self.content if isinstance(block, TextOutput))


class TextDelta(AIModel):
    type: Literal["text_delta"] = "text_delta"
    text: str
    block_index: int = 0


class ToolCallDelta(AIModel):
    type: Literal["tool_call_delta"] = "tool_call_delta"
    call_index: int
    arguments_delta: str


StreamEvent = TextDelta | ToolCallDelta


class RetryPolicy(AIModel):
    max_attempts: int = Field(default=3, ge=1)
    initial_delay_seconds: float = Field(default=0.5, ge=0)
    maximum_delay_seconds: float = Field(default=8.0, ge=0)


class MediaPolicy(AIModel):
    allow_local_files: bool = False
    allow_remote_urls: bool = False
    allowed_roots: tuple[str, ...] = ()
    allowed_domains: tuple[str, ...] = ()
    maximum_bytes: int = Field(default=10_000_000, gt=0)


class RedactionPolicy(AIModel):
    persist_inputs: bool = False
    persist_outputs: bool = False
    trace_content: bool = False


class HostedProvider(AIModel):
    kind: Literal["hosted"] = "hosted"
    api_key: SecretStr | None = Field(default=None, repr=False)
    api_base: str | None = None
    timeout: float | None = None


class OpenAICompatibleProvider(AIModel):
    kind: Literal["openai_compatible"] = "openai_compatible"
    base_url: str
    api_key: SecretStr | None = Field(default=None, repr=False)
    timeout: float | None = None


ProviderConfig = HostedProvider | OpenAICompatibleProvider