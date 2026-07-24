"""Versioned deterministic prompt assets."""

from __future__ import annotations

import hashlib
from string import Formatter
from typing import Any

from pydantic import Field

from qrt.ai.types import AIModel


class Prompt(AIModel):
    name: str
    version: str
    template: str
    variables: tuple[str, ...] = ()
    output_schema: dict[str, Any] | None = None
    examples: tuple[dict[str, Any], ...] = ()
    change_notes: str | None = None

    def model_post_init(self, context: Any) -> None:
        del context
        discovered = {field for _, field, _, _ in Formatter().parse(self.template) if field}
        declared = set(self.variables)
        if discovered != declared:
            raise ValueError(f"prompt variables must be exactly {sorted(discovered)}")

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.template.encode()).hexdigest()

    def render(self, **variables: Any) -> RenderedPrompt:
        if set(variables) != set(self.variables):
            raise ValueError(f"expected prompt variables {sorted(self.variables)}")
        text = self.template.format(**variables)
        return RenderedPrompt(
            name=self.name,
            version=self.version,
            text=text,
            prompt_hash=self.content_hash,
            rendered_hash=hashlib.sha256(text.encode()).hexdigest(),
        )


class RenderedPrompt(AIModel):
    name: str
    version: str
    text: str
    prompt_hash: str
    rendered_hash: str