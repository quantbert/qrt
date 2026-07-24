"""LiteLLM transport adapter for hosted and OpenAI-compatible providers."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from qrt._optional import missing_optional_dependency
from qrt.ai._backend import BackendRequest, BackendResponse
from qrt.ai.errors import CapabilityError
from qrt.ai.types import (
    CapabilityFact,
    CitationOutput,
    HostedProvider,
    ImageURLInput,
    Message,
    OpenAICompatibleProvider,
    RefusalOutput,
    TextDelta,
    TextInput,
    TextOutput,
    ToolCallOutput,
    UnknownOutput,
    Usage,
)


def _litellm():
    try:
        import litellm
    except ModuleNotFoundError as exc:
        if exc.name == "litellm":
            missing_optional_dependency(
                namespace="q.ai",
                extra="ai",
                dependency="litellm",
            )
        raise
    return litellm


def _plain(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    return vars(value)


def _message(message: Message) -> dict[str, Any]:
    blocks: list[dict[str, Any]] = []
    for block in message.content:
        if isinstance(block, TextInput):
            blocks.append({"type": "text", "text": block.text})
        elif isinstance(block, ImageURLInput):
            blocks.append({"type": "image_url", "image_url": {"url": block.url}})
        else:
            raise CapabilityError(
                f"LiteLLM transport does not transfer {block.type!r} references; "
                "use an explicit media resolver permitted by the client policy"
            )
    if len(blocks) == 1 and blocks[0]["type"] == "text":
        content: Any = blocks[0]["text"]
    else:
        content = blocks
    return {"role": message.role, "content": content}


def _usage(response: dict[str, Any]) -> Usage | None:
    value = response.get("usage")
    if value is None:
        return None
    data = _plain(value)
    known = {
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "cache_read_input_tokens",
        "reasoning_tokens",
    }
    return Usage(
        input_tokens=data.get("prompt_tokens"),
        output_tokens=data.get("completion_tokens"),
        cached_tokens=data.get("cache_read_input_tokens"),
        reasoning_tokens=data.get("reasoning_tokens"),
        total_tokens=data.get("total_tokens"),
        details={key: value for key, value in data.items() if key not in known and value is not None},
    )


def _content(message: dict[str, Any]) -> tuple[Any, ...]:
    blocks: list[Any] = []
    content = message.get("content")
    if isinstance(content, str) and content:
        blocks.append(TextOutput(text=content))
    elif isinstance(content, list):
        for item in content:
            data = _plain(item)
            kind = data.get("type")
            if kind in {"text", "output_text"}:
                blocks.append(TextOutput(text=data.get("text", "")))
            elif kind == "refusal":
                blocks.append(RefusalOutput(reason=data.get("refusal") or data.get("reason", "")))
            elif kind == "citation":
                blocks.append(CitationOutput(source_id=str(data.get("source_id", ""))))
            else:
                blocks.append(UnknownOutput(provider_type=str(kind or "unknown"), data=data))
    refusal = message.get("refusal")
    if refusal:
        blocks.append(RefusalOutput(reason=str(refusal)))
    for call in message.get("tool_calls") or ():
        data = _plain(call)
        function = _plain(data.get("function", {}))
        arguments = function.get("arguments", {})
        if isinstance(arguments, str):
            import json

            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {"_raw": arguments}
        blocks.append(
            ToolCallOutput(
                call_id=str(data.get("id", "")),
                name=str(function.get("name", "")),
                arguments=arguments,
            )
        )
    return tuple(blocks)


class LiteLLMBackend:
    """Private backend using LiteLLM for provider transport."""

    def __init__(self, config: HostedProvider | OpenAICompatibleProvider) -> None:
        self.config = config

    def _kwargs(self, request: BackendRequest, *, stream: bool = False) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": request.model.name,
            "messages": [_message(message) for message in request.messages],
            "num_retries": 0,
            "stream": stream,
            **request.provider_options,
        }
        values = {
            "temperature": request.temperature,
            "top_p": request.top_p,
            "max_completion_tokens": request.max_output_tokens,
            "stop": list(request.stop) or None,
            "seed": request.seed,
            "timeout": request.timeout or self.config.timeout,
        }
        kwargs.update({key: value for key, value in values.items() if value is not None})
        if request.output_schema is not None:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "qrt_output", "schema": request.output_schema, "strict": True},
            }
        if isinstance(self.config, OpenAICompatibleProvider):
            kwargs["base_url"] = self.config.base_url
        if self.config.api_key is not None:
            kwargs["api_key"] = self.config.api_key.get_secret_value()
        return kwargs

    def _response(self, value: Any, request: BackendRequest) -> BackendResponse:
        data = _plain(value)
        choices = data.get("choices") or []
        choice = _plain(choices[0]) if choices else {}
        message = _plain(choice.get("message", {}))
        try:
            integration_version = version("litellm")
        except PackageNotFoundError:
            integration_version = None
        return BackendResponse(
            resolved_model=str(data.get("model") or request.model.name),
            content=_content(message),
            usage=_usage(data),
            finish_reason=choice.get("finish_reason"),
            request_id=data.get("id"),
            raw=value if request.include_raw else None,
            integration="litellm",
            integration_version=integration_version,
            structured_mechanism="provider_json_schema" if request.output_schema else None,
        )

    def generate(self, request: BackendRequest) -> BackendResponse:
        response = _litellm().completion(**self._kwargs(request))
        return self._response(response, request)

    async def agenerate(self, request: BackendRequest) -> BackendResponse:
        response = await _litellm().acompletion(**self._kwargs(request))
        return self._response(response, request)

    def stream(self, request: BackendRequest) -> Iterator[TextDelta]:
        response = _litellm().completion(**self._kwargs(request, stream=True))
        for chunk in response:
            data = _plain(chunk)
            choices = data.get("choices") or []
            if not choices:
                continue
            delta = _plain(_plain(choices[0]).get("delta", {}))
            if delta.get("content"):
                yield TextDelta(text=delta["content"])

    async def astream(self, request: BackendRequest) -> AsyncIterator[TextDelta]:
        response = await _litellm().acompletion(**self._kwargs(request, stream=True))
        async for chunk in response:
            data = _plain(chunk)
            choices = data.get("choices") or []
            if not choices:
                continue
            delta = _plain(_plain(choices[0]).get("delta", {}))
            if delta.get("content"):
                yield TextDelta(text=delta["content"])

    def capabilities(self, model) -> dict[str, CapabilityFact]:
        del model
        return {
            "generation": CapabilityFact(status="supported", source="backend"),
            "streaming": CapabilityFact(status="supported", source="backend"),
            "structured_output": CapabilityFact(status="unknown", source="backend"),
        }