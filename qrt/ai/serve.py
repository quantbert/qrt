"""Validated local inference-server specifications."""

from __future__ import annotations

from typing import Literal

import requests
from pydantic import Field

from qrt.ai.types import AIModel


class LoRADeployment(AIModel):
    name: str
    path: str
    revision: str | None = None


class ServerSpec(AIModel):
    engine: Literal["vllm", "sglang", "llama.cpp"]
    model: str
    served_model_name: str | None = None
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    revision: str | None = None
    tensor_parallel_size: int = Field(default=1, ge=1)
    adapters: tuple[LoRADeployment, ...] = ()

    def command(self) -> list[str]:
        if self.engine == "vllm":
            command = ["vllm", "serve", self.model, "--host", self.host, "--port", str(self.port)]
            if self.served_model_name:
                command += ["--served-model-name", self.served_model_name]
            if self.tensor_parallel_size != 1:
                command += ["--tensor-parallel-size", str(self.tensor_parallel_size)]
            if self.adapters:
                command += ["--enable-lora", "--lora-modules", *[f"{item.name}={item.path}" for item in self.adapters]]
            return command
        if self.engine == "sglang":
            return ["python", "-m", "sglang.launch_server", "--model-path", self.model, "--host", self.host, "--port", str(self.port)]
        return ["llama-server", "-m", self.model, "--host", self.host, "--port", str(self.port)]

    def health(self, timeout: float = 2.0) -> bool:
        try:
            response = requests.get(f"http://{self.host}:{self.port}/health", timeout=timeout)
        except requests.RequestException:
            return False
        return response.ok