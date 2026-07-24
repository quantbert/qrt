"""Typed, allowlisted tool definitions and execution."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

from qrt.ai.errors import AIError

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class ToolExecutionError(AIError):
    """A validated tool failed or exceeded its execution policy."""


class Tool(Generic[InputT, OutputT]):
    """A typed local tool whose callable is never selected by model output."""

    def __init__(
        self,
        function: Callable[[InputT], OutputT | dict[str, Any]],
        *,
        name: str,
        input: type[InputT],
        output: type[OutputT],
        description: str = "",
        timeout: float = 30.0,
    ) -> None:
        self.function = function
        self.name = name
        self.input_type = input
        self.output_type = output
        self.description = description
        self.timeout = timeout

    @property
    def parameters(self) -> dict[str, Any]:
        return self.input_type.model_json_schema()

    @property
    def returns(self) -> dict[str, Any]:
        return self.output_type.model_json_schema()

    def execute(self, value: InputT | dict[str, Any]) -> OutputT:
        arguments = value if isinstance(value, self.input_type) else self.input_type.model_validate(value)
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self.function, arguments)
        try:
            result = future.result(timeout=self.timeout)
        except TimeoutError as exc:
            future.cancel()
            raise ToolExecutionError(f"tool {self.name!r} exceeded {self.timeout} seconds") from exc
        except Exception as exc:
            raise ToolExecutionError(f"tool {self.name!r} failed: {exc}") from exc
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
        return self.output_type.model_validate(result)

    def as_pydantic_ai(self):
        from pydantic_ai import Tool as PydanticTool

        def invoke(**arguments: Any) -> dict[str, Any]:
            return self.execute(arguments).model_dump(mode="json")

        return PydanticTool.from_schema(
            invoke,
            name=self.name,
            description=self.description,
            json_schema=self.parameters,
        )


class ToolRegistry:
    """Explicit allowlist for safe local tool execution."""

    def __init__(self, tools: list[Tool[Any, Any]] | None = None) -> None:
        self._tools = {tool.name: tool for tool in (tools or [])}

    def register(self, tool: Tool[Any, Any]) -> None:
        if tool.name in self._tools:
            raise ValueError(f"tool {tool.name!r} is already registered")
        self._tools[tool.name] = tool

    def execute(self, name: str, arguments: dict[str, Any]) -> BaseModel:
        if name not in self._tools:
            raise ToolExecutionError(f"tool {name!r} is not allowlisted")
        return self._tools[name].execute(arguments)

    def pydantic_ai_tools(self) -> list[Any]:
        return [tool.as_pydantic_ai() for tool in self._tools.values()]


def tool(*, name: str, input: type[InputT], output: type[OutputT], description: str = "", timeout: float = 30.0):
    """Decorate a callable as a typed QRT tool."""
    def decorate(function: Callable[[InputT], OutputT | dict[str, Any]]) -> Tool[InputT, OutputT]:
        return Tool(function, name=name, input=input, output=output, description=description, timeout=timeout)

    return decorate