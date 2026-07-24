"""Explicit context-managed local model engines."""

from __future__ import annotations

from typing import Any


class TransformersEngine:
    """Own a Transformers model, tokenizer, PEFT adapters, and device resources."""

    def __init__(
        self,
        model: str,
        *,
        adapters: dict[str, str] | None = None,
        device_map: str | dict[str, Any] = "auto",
        quantization_config: Any | None = None,
        revision: str | None = None,
    ) -> None:
        self.model_id = model
        self.adapters = dict(adapters or {})
        self.device_map = device_map
        self.quantization_config = quantization_config
        self.revision = revision
        self.model = None
        self.tokenizer = None

    def __enter__(self) -> TransformersEngine:
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, revision=self.revision)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            revision=self.revision,
            device_map=self.device_map,
            quantization_config=self.quantization_config,
        )
        if self.adapters:
            from peft import PeftModel

            first_name, first_path = next(iter(self.adapters.items()))
            self.model = PeftModel.from_pretrained(self.model, first_path, adapter_name=first_name)
            for name, path in list(self.adapters.items())[1:]:
                self.model.load_adapter(path, adapter_name=name)
        return self

    def generate(self, prompt: str, *, adapter: str | None = None, **options: Any) -> str:
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("TransformersEngine must be used as a context manager")
        if adapter is not None and hasattr(self.model, "set_adapter"):
            self.model.set_adapter(adapter)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        generated = self.model.generate(**inputs, **options)
        return self.tokenizer.decode(generated[0], skip_special_tokens=True)

    def __exit__(self, *_: object) -> None:
        self.model = None
        self.tokenizer = None
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ModuleNotFoundError:
            pass