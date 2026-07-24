import asyncio
import json

import pytest
from pydantic import BaseModel

import qrt as q
from qrt.ai._backend import MemoryBackend


def client(response: str = "hello world") -> q.ai.Client:
    return q.ai.Client(
        providers={"test": q.ai.HostedProvider()},
        _backends={"test": MemoryBackend(response)},
    )


def test_generation_normalizes_text_usage_and_provenance():
    result = client().generate(
        model="test/example/model",
        messages=[q.ai.SystemMessage("Be concise."), q.ai.UserMessage("Hello")],
        max_output_tokens=10,
        request_context={"experiment_id": "not-outbound"},
    )

    assert result.text == "hello world"
    assert result.logical_model == q.ai.ModelRef(provider="test", name="example/model")
    assert result.usage.output_tokens == 2
    assert result.provenance.prompt_hash
    assert result.provenance.options_hash
    assert result.raw is None


def test_deployment_alias_preserves_lineage():
    configured = q.ai.Client(
        providers={"local": q.ai.HostedProvider()},
        deployments={
            "filings": q.ai.ModelDeployment(
                model=q.ai.ModelRef(provider="local", name="filings-adapter"),
                revision="deploy-3",
                base_model="base@abc",
                adapter="adapter@def",
            )
        },
        _backends={"local": MemoryBackend("ok")},
    )

    result = configured.generate(model="filings", messages=[q.ai.UserMessage("x")])

    assert result.provenance.deployment_revision == "deploy-3"
    assert result.provenance.base_model == "base@abc"
    assert result.provenance.adapter == "adapter@def"


def test_model_resolution_uses_longest_provider_prefix():
    configured = q.ai.Client(
        providers={"local": q.ai.HostedProvider(), "local/research": q.ai.HostedProvider()},
        _backends={"local/research": MemoryBackend("ok")},
    )

    result = configured.generate(
        model="local/research/org/model",
        messages=[q.ai.UserMessage("x")],
    )

    assert result.logical_model.provider == "local/research"
    assert result.logical_model.name == "org/model"


def test_structured_extraction_validates_pydantic_output():
    class Risk(BaseModel):
        severity: str

    result = client(json.dumps({"severity": "high"})).extract(
        model="test/model",
        input="extract",
        output=Risk,
    )

    assert result.structured == Risk(severity="high")
    assert result.provenance.schema_hash
    assert result.provenance.structured_mechanism == "test"


def test_structured_extraction_distinguishes_parse_and_validation_errors():
    class Risk(BaseModel):
        severity: int

    with pytest.raises(q.ai.StructuredOutputParseError):
        client("not json").extract(model="test/model", input="x", output=Risk)
    with pytest.raises(q.ai.StructuredOutputValidationError):
        client('{"severity": "high"}').extract(model="test/model", input="x", output=Risk)


def test_stream_assembles_final_result():
    with client().stream(model="test/model", messages=[q.ai.UserMessage("x")]) as stream:
        observed = "".join(event.text for event in stream)

    assert observed == "hello world "
    assert stream.result.text == "hello world"


def test_async_generation_and_streaming():
    async def run():
        configured = client()
        result = await configured.agenerate(
            model="test/model", messages=[q.ai.UserMessage("x")]
        )
        async with configured.astream(
            model="test/model", messages=[q.ai.UserMessage("x")]
        ) as stream:
            observed = [event.text async for event in stream]
        return result, observed, stream.result

    result, observed, final = asyncio.run(run())
    assert result.text == "hello world"
    assert observed == ["hello ", "world "]
    assert final.text == "hello world"


def test_provider_secrets_are_not_represented_or_serialized():
    provider = q.ai.HostedProvider(api_key="super-secret")

    assert "super-secret" not in repr(provider)
    assert "super-secret" not in provider.model_dump_json()


def test_generation_joins_active_experiment_without_logging_content(tmp_path):
    tracker = q.experiment.LocalTracker(tmp_path)
    configured = client("sensitive output")

    with tracker.run("research-run") as run:
        result = configured.generate(
            model="test/model",
            messages=[q.ai.UserMessage("sensitive prompt")],
        )

    assert result.provenance.experiment_run_id == run.run_id
    stored = tracker.get_run(run.run_id)
    records = [item for item in stored["values"] if item["kind"] == "ai/inference"]
    assert len(records) == 1
    serialized = json.dumps(records[0]["value"])
    assert "sensitive prompt" not in serialized
    assert "sensitive output" not in serialized
    assert records[0]["value"]["prompt_hash"] == result.provenance.prompt_hash


def test_client_tracker_creates_a_standalone_inference_run(tmp_path):
    tracker = q.experiment.LocalTracker(tmp_path)
    configured = q.ai.Client(
        providers={"test": q.ai.HostedProvider()},
        tracker=tracker,
        _backends={"test": MemoryBackend("tracked")},
    )

    result = configured.generate(
        model="test/model",
        messages=[q.ai.UserMessage("hello")],
    )

    stored = tracker.get_run(result.provenance.experiment_run_id)
    assert stored["name"] == "q.ai.generate"
    assert stored["status"] == "FINISHED"