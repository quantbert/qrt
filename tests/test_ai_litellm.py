import asyncio
from types import SimpleNamespace

import pytest

import qrt as q


pytest.importorskip("litellm")


def response(content="answer", *, raw_id="req-1"):
    return SimpleNamespace(
        id=raw_id,
        model="resolved/model",
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content, refusal=None, tool_calls=None),
                finish_reason="stop",
            )
        ],
        usage=SimpleNamespace(prompt_tokens=3, completion_tokens=2, total_tokens=5),
        model_dump=lambda: {
            "id": raw_id,
            "model": "resolved/model",
            "choices": [
                {
                    "message": {"content": content, "refusal": None, "tool_calls": None},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
        },
    )


def configured_client():
    return q.ai.Client(
        providers={
            "local": q.ai.OpenAICompatibleProvider(
                base_url="http://127.0.0.1:8000/v1", api_key="secret"
            )
        }
    )


def test_litellm_request_translation_and_raw_opt_in(monkeypatch):
    import litellm

    observed = {}

    def completion(**kwargs):
        observed.update(kwargs)
        return response()

    monkeypatch.setattr(litellm, "completion", completion)
    result = configured_client().generate(
        model="local/org/model",
        messages=[q.ai.UserMessage("hello")],
        max_output_tokens=50,
        provider_options={"verbosity": "low"},
        include_raw=True,
    )

    assert observed["model"] == "org/model"
    assert observed["messages"] == [{"role": "user", "content": "hello"}]
    assert observed["max_completion_tokens"] == 50
    assert observed["num_retries"] == 0
    assert observed["base_url"] == "http://127.0.0.1:8000/v1"
    assert observed["api_key"] == "secret"
    assert observed["verbosity"] == "low"
    assert result.text == "answer"
    assert result.usage.total_tokens == 5
    assert result.raw is not None
    assert "raw" not in result.model_dump()


def test_litellm_structured_schema_and_async_generation(monkeypatch):
    import litellm
    from pydantic import BaseModel

    class Item(BaseModel):
        value: int

    observed = {}

    async def acompletion(**kwargs):
        observed.update(kwargs)
        return response('{"value": 4}')

    monkeypatch.setattr(litellm, "acompletion", acompletion)

    async def run():
        client = configured_client()
        return await client.agenerate(
            model="local/model", messages=[q.ai.UserMessage("hello")]
        )

    assert asyncio.run(run()).text == '{"value": 4}'

    def completion(**kwargs):
        observed.update(kwargs)
        return response('{"value": 4}')

    monkeypatch.setattr(litellm, "completion", completion)
    extracted = configured_client().extract(
        model="local/model", input="extract", output=Item
    )
    assert observed["response_format"]["type"] == "json_schema"
    assert observed["response_format"]["json_schema"]["strict"] is True
    assert extracted.structured.value == 4


def test_litellm_streaming(monkeypatch):
    import litellm

    chunks = [
        {"choices": [{"delta": {"content": "hel"}}]},
        {"choices": [{"delta": {"content": "lo"}}]},
    ]
    monkeypatch.setattr(litellm, "completion", lambda **kwargs: iter(chunks))

    with configured_client().stream(
        model="local/model", messages=[q.ai.UserMessage("x")]
    ) as stream:
        assert "".join(event.text for event in stream) == "hello"
    assert stream.result.text == "hello"


def test_local_media_is_inert_and_not_transferred(monkeypatch):
    import litellm

    monkeypatch.setattr(litellm, "completion", lambda **kwargs: response())
    message = q.ai.UserMessage(
        (q.ai.TextInput(text="inspect"), q.ai.ImagePathInput(path="secret.png"))
    )

    try:
        configured_client().generate(model="local/model", messages=[message])
    except q.ai.CapabilityError as exc:
        assert "does not transfer" in str(exc)
    else:
        raise AssertionError("an inert local path must not be transferred")