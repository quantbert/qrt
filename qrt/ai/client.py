"""Configured client for repeatable QRT AI workflows."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections.abc import AsyncIterator, Iterator, Mapping, Sequence
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import BaseModel, ValidationError

from qrt.ai._backend import Backend, BackendRequest, BackendResponse
from qrt.ai.errors import (
    ModelResolutionError,
    StreamClosedError,
    StructuredOutputParseError,
    StructuredOutputValidationError,
)
from qrt.ai.types import (
    GenerationResult,
    InferenceProvenance,
    MediaPolicy,
    Message,
    ModelDeployment,
    ModelRef,
    ProviderConfig,
    RedactionPolicy,
    RetryPolicy,
    StreamEvent,
    TextDelta,
)

T = TypeVar("T", bound=BaseModel)

if TYPE_CHECKING:
    from qrt.experiment import Tracker


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


class Stream:
    """Synchronous stream with deterministic cleanup and a final result."""

    def __init__(self, client: Client, request: BackendRequest, deployment: ModelDeployment | None) -> None:
        self._client = client
        self._request = request
        self._deployment = deployment
        self._events: Iterator[TextDelta] | None = None
        self._result: GenerationResult[Any] | None = None
        self._cancelled = False

    def __enter__(self) -> Stream:
        self._events = self._client._backend_for(self._request.model.provider).stream(self._request)
        return self

    def __iter__(self) -> Iterator[StreamEvent]:
        if self._events is None:
            raise RuntimeError("stream must be used as a context manager")
        text: list[str] = []
        for event in self._events:
            if self._cancelled:
                break
            text.append(event.text)
            yield event
        self._result = self._client._result_from_stream(
            self._request,
            "".join(text).rstrip(),
            self._deployment,
            cancelled=self._cancelled,
        )

    def cancel(self) -> None:
        self._cancelled = True

    @property
    def result(self) -> GenerationResult[Any]:
        if self._result is None:
            raise StreamClosedError("consume or cancel the stream before requesting its result")
        return self._result

    def __exit__(self, *_: object) -> None:
        close = getattr(self._events, "close", None)
        if close is not None:
            close()


class AsyncStream:
    """Asynchronous stream with deterministic cleanup and a final result."""

    def __init__(self, client: Client, request: BackendRequest, deployment: ModelDeployment | None) -> None:
        self._client = client
        self._request = request
        self._deployment = deployment
        self._events: AsyncIterator[TextDelta] | None = None
        self._result: GenerationResult[Any] | None = None
        self._cancelled = False

    async def __aenter__(self) -> AsyncStream:
        self._events = self._client._backend_for(self._request.model.provider).astream(self._request)
        return self

    async def __aiter__(self) -> AsyncIterator[StreamEvent]:
        if self._events is None:
            raise RuntimeError("stream must be used as an async context manager")
        text: list[str] = []
        async for event in self._events:
            if self._cancelled:
                break
            text.append(event.text)
            yield event
        self._result = self._client._result_from_stream(
            self._request,
            "".join(text).rstrip(),
            self._deployment,
            cancelled=self._cancelled,
        )

    def cancel(self) -> None:
        self._cancelled = True

    @property
    def result(self) -> GenerationResult[Any]:
        if self._result is None:
            raise StreamClosedError("consume or cancel the stream before requesting its result")
        return self._result

    async def __aexit__(self, *_: object) -> None:
        close = getattr(self._events, "aclose", None)
        if close is not None:
            await close()


class Client:
    """Immutable configuration boundary for QRT AI operations."""

    def __init__(
        self,
        *,
        providers: Mapping[str, ProviderConfig] | None = None,
        deployments: Mapping[str, ModelDeployment | ModelRef] | None = None,
        retry: RetryPolicy | None = None,
        media: MediaPolicy | None = None,
        redaction: RedactionPolicy | None = None,
        tracker: Tracker | None = None,
        strict_capabilities: bool = False,
        _backends: Mapping[str, Backend] | None = None,
    ) -> None:
        self.providers = dict(providers or {})
        self.deployments = {
            alias: value if isinstance(value, ModelDeployment) else ModelDeployment(model=value)
            for alias, value in (deployments or {}).items()
        }
        self.retry = retry or RetryPolicy()
        self.media = media or MediaPolicy()
        self.redaction = redaction or RedactionPolicy()
        self.tracker = tracker
        self.strict_capabilities = strict_capabilities
        self._backends = dict(_backends or {})

    def _backend_for(self, provider: str) -> Backend:
        if provider in self._backends:
            return self._backends[provider]
        from qrt.ai._integrations.litellm import LiteLLMBackend

        if provider not in self.providers:
            raise ModelResolutionError(f"provider {provider!r} is not configured")
        backend = LiteLLMBackend(self.providers[provider])
        self._backends[provider] = backend
        return backend

    def resolve_model(self, model: str | ModelRef) -> tuple[ModelRef, ModelDeployment | None]:
        if isinstance(model, ModelRef):
            return model, None
        if model in self.deployments:
            deployment = self.deployments[model]
            return deployment.model, deployment
        matches = [prefix for prefix in self.providers if model.startswith(f"{prefix}/")]
        if matches:
            provider = max(matches, key=len)
            return ModelRef(provider=provider, name=model[len(provider) + 1 :]), None
        raise ModelResolutionError(
            f"model {model!r} is not a deployment alias or provider-qualified model"
        )

    def _request(
        self,
        *,
        model: str | ModelRef,
        messages: Sequence[Message],
        temperature: float | None,
        top_p: float | None,
        max_output_tokens: int | None,
        stop: Sequence[str] | None,
        seed: int | None,
        timeout: float | None,
        output_schema: dict[str, Any] | None,
        provider_options: Mapping[str, Any] | None,
        include_raw: bool,
    ) -> tuple[BackendRequest, ModelDeployment | None]:
        model_ref, deployment = self.resolve_model(model)
        return BackendRequest(
            model=model_ref,
            messages=tuple(messages),
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            stop=tuple(stop or ()),
            seed=seed,
            timeout=timeout,
            output_schema=output_schema,
            provider_options=dict(provider_options or {}),
            include_raw=include_raw,
        ), deployment

    def generate(
        self,
        *,
        model: str | ModelRef,
        messages: Sequence[Message],
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        stop: Sequence[str] | None = None,
        seed: int | None = None,
        timeout: float | None = None,
        request_context: Mapping[str, Any] | None = None,
        provider_options: Mapping[str, Any] | None = None,
        include_raw: bool = False,
    ) -> GenerationResult[Any]:
        request, deployment = self._request(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            stop=stop,
            seed=seed,
            timeout=timeout,
            output_schema=None,
            provider_options=provider_options,
            include_raw=include_raw,
        )
        del request_context
        started = datetime.now(timezone.utc)
        response = self._backend_for(request.model.provider).generate(request)
        result = self._normalize(request, response, deployment, started)
        return self._track_result(result, operation="generate")

    async def agenerate(self, **kwargs: Any) -> GenerationResult[Any]:
        request, deployment = self._request(
            model=kwargs.pop("model"),
            messages=kwargs.pop("messages"),
            temperature=kwargs.pop("temperature", None),
            top_p=kwargs.pop("top_p", None),
            max_output_tokens=kwargs.pop("max_output_tokens", None),
            stop=kwargs.pop("stop", None),
            seed=kwargs.pop("seed", None),
            timeout=kwargs.pop("timeout", None),
            output_schema=None,
            provider_options=kwargs.pop("provider_options", None),
            include_raw=kwargs.pop("include_raw", False),
        )
        kwargs.pop("request_context", None)
        if kwargs:
            raise TypeError(f"unexpected generation options: {sorted(kwargs)}")
        started = datetime.now(timezone.utc)
        response = await self._backend_for(request.model.provider).agenerate(request)
        result = self._normalize(request, response, deployment, started)
        return self._track_result(result, operation="generate")

    def extract(
        self,
        *,
        model: str | ModelRef,
        input: str,
        output: type[T],
        max_repair_attempts: int = 0,
        **kwargs: Any,
    ) -> GenerationResult[T]:
        from qrt.ai.types import UserMessage

        schema = output.model_json_schema()
        request, deployment = self._request(
            model=model,
            messages=(UserMessage(input),),
            temperature=kwargs.pop("temperature", None),
            top_p=kwargs.pop("top_p", None),
            max_output_tokens=kwargs.pop("max_output_tokens", None),
            stop=kwargs.pop("stop", None),
            seed=kwargs.pop("seed", None),
            timeout=kwargs.pop("timeout", None),
            output_schema=schema,
            provider_options=kwargs.pop("provider_options", None),
            include_raw=kwargs.pop("include_raw", False),
        )
        if kwargs:
            raise TypeError(f"unexpected extraction options: {sorted(kwargs)}")
        attempts = 0
        while True:
            started = datetime.now(timezone.utc)
            response = self._backend_for(request.model.provider).generate(request)
            normalized = self._normalize(request, response, deployment, started, schema=schema)
            try:
                payload = json.loads(normalized.text)
            except json.JSONDecodeError as exc:
                error: Exception = StructuredOutputParseError(str(exc))
            else:
                try:
                    value = output.model_validate(payload)
                except ValidationError as exc:
                    error = StructuredOutputValidationError(str(exc))
                else:
                    structured = normalized.model_copy(update={"structured": value})
                    return self._track_result(structured, operation="extract")
            if attempts >= max_repair_attempts:
                raise error
            attempts += 1

    def stream(self, *, model: str | ModelRef, messages: Sequence[Message], **kwargs: Any) -> Stream:
        request, deployment = self._request(
            model=model,
            messages=messages,
            temperature=kwargs.pop("temperature", None),
            top_p=kwargs.pop("top_p", None),
            max_output_tokens=kwargs.pop("max_output_tokens", None),
            stop=kwargs.pop("stop", None),
            seed=kwargs.pop("seed", None),
            timeout=kwargs.pop("timeout", None),
            output_schema=None,
            provider_options=kwargs.pop("provider_options", None),
            include_raw=kwargs.pop("include_raw", False),
        )
        if kwargs:
            raise TypeError(f"unexpected streaming options: {sorted(kwargs)}")
        return Stream(self, request, deployment)

    def astream(self, *, model: str | ModelRef, messages: Sequence[Message], **kwargs: Any) -> AsyncStream:
        request, deployment = self._request(
            model=model,
            messages=messages,
            temperature=kwargs.pop("temperature", None),
            top_p=kwargs.pop("top_p", None),
            max_output_tokens=kwargs.pop("max_output_tokens", None),
            stop=kwargs.pop("stop", None),
            seed=kwargs.pop("seed", None),
            timeout=kwargs.pop("timeout", None),
            output_schema=None,
            provider_options=kwargs.pop("provider_options", None),
            include_raw=kwargs.pop("include_raw", False),
        )
        if kwargs:
            raise TypeError(f"unexpected streaming options: {sorted(kwargs)}")
        return AsyncStream(self, request, deployment)

    def _normalize(
        self,
        request: BackendRequest,
        response: BackendResponse,
        deployment: ModelDeployment | None,
        started: datetime,
        *,
        schema: dict[str, Any] | None = None,
    ) -> GenerationResult[Any]:
        import qrt

        prompt = [message.model_dump(mode="json") for message in request.messages]
        options = {
            "temperature": request.temperature,
            "top_p": request.top_p,
            "max_output_tokens": request.max_output_tokens,
            "stop": request.stop,
            "seed": request.seed,
        }
        provenance = InferenceProvenance(
            logical_model=request.model,
            resolved_model=response.resolved_model,
            provider=request.model.provider,
            deployment_revision=deployment.revision if deployment else None,
            base_model=deployment.base_model if deployment else None,
            adapter=deployment.adapter if deployment else None,
            prompt_hash=_stable_hash(prompt),
            schema_hash=_stable_hash(schema) if schema else None,
            options_hash=_stable_hash(options),
            provider_options_hash=_stable_hash(request.provider_options) if request.provider_options else None,
            structured_mechanism=response.structured_mechanism,
            qrt_version=qrt.__version__,
            integration=response.integration,
            integration_version=response.integration_version,
            started_at=started,
            completed_at=datetime.now(timezone.utc),
        )
        finish_reason = response.finish_reason
        portable_finish = finish_reason if finish_reason in {"stop", "length", "tool_call", "refusal", "cancelled", "error"} else "unknown"
        return GenerationResult(
            logical_model=request.model,
            resolved_model=response.resolved_model,
            content=response.content,
            usage=response.usage,
            finish_reason=portable_finish,
            provider_finish_reason=finish_reason,
            request_id=response.request_id,
            provenance=provenance,
            raw=response.raw if request.include_raw else None,
        )

    def _result_from_stream(
        self,
        request: BackendRequest,
        text: str,
        deployment: ModelDeployment | None,
        *,
        cancelled: bool,
    ) -> GenerationResult[Any]:
        from qrt.ai.types import TextOutput

        started = datetime.now(timezone.utc)
        response = BackendResponse(
            resolved_model=str(request.model),
            content=(TextOutput(text=text),),
            finish_reason="cancelled" if cancelled else "stop",
            integration="stream",
        )
        result = self._normalize(request, response, deployment, started)
        return self._track_result(result, operation="stream")

    def _track_result(
        self,
        result: GenerationResult[Any],
        *,
        operation: str,
    ) -> GenerationResult[Any]:
        from qrt.experiment import active_run

        run = active_run()
        if run is not None:
            return self._log_result(run, result, operation=operation)
        if self.tracker is None:
            return result
        with self.tracker.run(
            f"q.ai.{operation}",
            tags={"qrt.namespace": "ai", "qrt.operation": operation},
        ) as run:
            return self._log_result(run, result, operation=operation)

    def _log_result(self, run, result: GenerationResult[Any], *, operation: str) -> GenerationResult[Any]:
        provenance = result.provenance.model_copy(update={"experiment_run_id": run.run_id})
        tracked = result.model_copy(update={"provenance": provenance})
        metrics = {}
        if result.usage is not None:
            usage = result.usage
            metrics = {
                key: float(value)
                for key, value in {
                    "ai.input_tokens": usage.input_tokens,
                    "ai.output_tokens": usage.output_tokens,
                    "ai.total_tokens": usage.total_tokens,
                    "ai.cost": usage.request_cost,
                    "ai.latency_seconds": usage.latency_seconds,
                }.items()
                if value is not None
            }
        if metrics:
            run.log_metrics(metrics)
        run.set_tags(
            {
                "qrt.namespace": "ai",
                "qrt.operation": operation,
                "qrt.ai.provider": provenance.provider,
            }
        )
        record_name = result.request_id or f"{operation}-{provenance.prompt_hash[:16]}"
        run.log_record(
            "ai/inference",
            record_name,
            {
                "logical_model": provenance.logical_model.model_dump(mode="json"),
                "resolved_model": provenance.resolved_model,
                "provider": provenance.provider,
                "deployment_revision": provenance.deployment_revision,
                "base_model": provenance.base_model,
                "adapter": provenance.adapter,
                "prompt_hash": provenance.prompt_hash,
                "schema_hash": provenance.schema_hash,
                "options_hash": provenance.options_hash,
                "provider_options_hash": provenance.provider_options_hash,
                "structured_mechanism": provenance.structured_mechanism,
                "integration": provenance.integration,
                "integration_version": provenance.integration_version,
                "finish_reason": result.finish_reason,
                "usage": result.usage.model_dump(mode="json") if result.usage else None,
            },
        )
        return tracked