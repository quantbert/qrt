import pytest

import qrt as q


def test_vllm_server_spec_addresses_adapters_as_models():
    spec = q.ai.serve.ServerSpec(
        engine="vllm",
        model="base/model",
        served_model_name="base",
        adapters=(q.ai.serve.LoRADeployment(name="filings", path="/adapters/filings"),),
    )
    command = spec.command()
    assert command[:3] == ["vllm", "serve", "base/model"]
    assert "filings=/adapters/filings" in command


def test_finetune_spec_requires_lineage():
    adapter = q.ai.finetune.AdapterConfig(target_modules=("q_proj", "v_proj"))
    spec = q.ai.finetune.TrainingSpec(
        base_model="base", base_revision="abc", tokenizer="tok", tokenizer_revision="def",
        dataset="filings", dataset_revision="ghi", output_dir="out", adapter=adapter,
    )
    assert spec.adapter.method == "lora"


def test_integrations_report_curated_statuses():
    pytest.importorskip("lancedb")
    statuses = {item.name: item for item in q.ai.integrations.report()}
    assert statuses["litellm"].status == "preferred"
    assert statuses["lancedb"].installed