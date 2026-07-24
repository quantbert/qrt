"""Model-aware token counting and context budgeting."""

from __future__ import annotations

from typing import Literal

from qrt.ai.types import AIModel


class TokenizationResult(AIModel):
    token_ids: tuple[int, ...]
    tokenizer: str
    revision: str | None = None
    exact: bool
    special_tokens: bool

    @property
    def count(self) -> int:
        return len(self.token_ids)


def encode(
    text: str,
    *,
    tokenizer: str,
    revision: str | None = None,
    add_special_tokens: bool = False,
    backend: Literal["huggingface", "tiktoken"] = "huggingface",
) -> TokenizationResult:
    """Tokenize text with an explicitly identified tokenizer."""
    if backend == "tiktoken":
        import tiktoken

        encoding = tiktoken.get_encoding(tokenizer)
        ids = encoding.encode(text)
    else:
        from transformers import AutoTokenizer

        resolved = AutoTokenizer.from_pretrained(tokenizer, revision=revision)
        ids = resolved.encode(text, add_special_tokens=add_special_tokens)
    return TokenizationResult(
        token_ids=tuple(ids), tokenizer=tokenizer, revision=revision, exact=True, special_tokens=add_special_tokens
    )


def truncate(result: TokenizationResult, maximum_tokens: int) -> TokenizationResult:
    return result.model_copy(update={"token_ids": result.token_ids[:maximum_tokens]})