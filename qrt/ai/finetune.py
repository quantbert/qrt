"""LoRA and QLoRA adaptation specifications with artifact lineage."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from qrt.ai.types import AIModel


class AdapterConfig(AIModel):
    method: Literal["lora", "qlora"] = "lora"
    rank: int = Field(default=16, ge=1)
    alpha: int = Field(default=32, ge=1)
    dropout: float = Field(default=0.05, ge=0, lt=1)
    target_modules: tuple[str, ...]


class TrainingSpec(AIModel):
    base_model: str
    base_revision: str
    tokenizer: str
    tokenizer_revision: str
    dataset: str
    dataset_revision: str
    output_dir: str
    adapter: AdapterConfig
    chat_template: str | None = None
    train_split: str = "train"
    eval_split: str = "validation"
    epochs: float = Field(default=1.0, gt=0)

    @model_validator(mode="after")
    def immutable_revisions(self):
        for field in ("base_revision", "tokenizer_revision", "dataset_revision"):
            if not getattr(self, field).strip():
                raise ValueError(f"{field} must identify an immutable revision")
        return self