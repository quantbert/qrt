"""Bounded Pydantic AI-backed agent workflows."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from qrt.ai.types import AIModel
from qrt.ai.tools import Tool, ToolRegistry

OutputT = TypeVar("OutputT", bound=BaseModel)


class AgentLimits(AIModel):
    max_steps: int = Field(default=8, ge=1)
    max_tool_calls: int | None = Field(default=None, ge=1)
    max_input_tokens: int | None = Field(default=None, ge=1)
    max_output_tokens: int | None = Field(default=None, ge=1)
    max_total_tokens: int | None = Field(default=None, ge=1)
    max_cost: float | None = Field(default=None, gt=0)


class AgentResult(AIModel, Generic[OutputT]):
    value: OutputT
    run_id: str | None = None
    usage: dict[str, Any]
    messages_json: bytes = Field(repr=False)


class Agent(Generic[OutputT]):
    """A typed bounded agent delegated to Pydantic AI."""

    def __init__(
        self,
        *,
        model: Any,
        tools: list[Tool[Any, Any]],
        output: type[OutputT],
        limits: AgentLimits | None = None,
        instructions: str | None = None,
    ) -> None:
        from pydantic_ai import Agent as PydanticAgent

        self.output_type = output
        self.limits = limits or AgentLimits()
        self.registry = ToolRegistry(tools)
        self._agent = PydanticAgent(
            model,
            output_type=output,
            instructions=instructions,
            tools=self.registry.pydantic_ai_tools(),
        )

    def run(self, prompt: str) -> AgentResult[OutputT]:
        from pydantic_ai.usage import UsageLimits

        result = self._agent.run_sync(
            prompt,
            usage_limits=UsageLimits(
                request_limit=self.limits.max_steps,
                tool_calls_limit=self.limits.max_tool_calls,
                input_tokens_limit=self.limits.max_input_tokens,
                output_tokens_limit=self.limits.max_output_tokens,
                total_tokens_limit=self.limits.max_total_tokens,
            ),
        )
        usage = result.usage()
        usage_data = usage.opentelemetry_attributes() if hasattr(usage, "opentelemetry_attributes") else vars(usage)
        return AgentResult(
            value=self.output_type.model_validate(result.output),
            run_id=result.run_id,
            usage=usage_data,
            messages_json=result.all_messages_json(),
        )