import subprocess
import sys

import pytest

import qrt as q


def test_local_experiment_run_records_research_lineage(tmp_path):
    tracker = q.experiment.LocalTracker(tmp_path / "tracking")
    artifact = tmp_path / "report.txt"
    artifact.write_text("result")

    with tracker.run("factor-study", tags={"team": "research"}) as run:
        assert q.experiment.active_run() is run
        run.log_params({"window": 20}, seed=7)
        run.log_metrics({"sharpe": 1.25}, step=3)
        run.log_dataset(
            "prices",
            fingerprint="sha256:abc",
            source="warehouse/prices",
            metadata={"as_of": "2026-06-30"},
        )
        run.log_model("signal", artifact=artifact, flavor="qrt.signal")
        copied = run.log_artifact(artifact, artifact_path="reports")

    assert q.experiment.active_run() is None
    assert run.status == "FINISHED"
    assert (tmp_path / "tracking" / "artifacts" / run.run_id / "reports" / "report.txt").exists()
    assert copied.endswith("reports/report.txt")

    stored = tracker.get_run(run.run_id)
    assert stored["status"] == "FINISHED"
    values = {(item["kind"], item["key"]): item for item in stored["values"]}
    assert values[("param", "window")]["value"] == 20
    assert values[("metric", "sharpe")]["value"] == 1.25
    assert values[("datasets", "prices")]["value"]["fingerprint"] == "sha256:abc"
    assert values[("models", "signal")]["value"]["flavor"] == "qrt.signal"
    tracker.close()


def test_failed_run_is_terminated_and_active_context_resets(tmp_path):
    tracker = q.experiment.LocalTracker(tmp_path)

    with pytest.raises(RuntimeError, match="failed deliberately"):
        with tracker.run("failure") as run:
            raise RuntimeError("failed deliberately")

    assert run.status == "FAILED"
    assert q.experiment.active_run() is None
    assert tracker.get_run(run.run_id)["status"] == "FAILED"


def test_experiment_namespace_is_lazy_on_root_import():
    code = """
import sys
import qrt
assert 'qrt.experiment' not in sys.modules
assert 'mlflow' not in sys.modules
assert qrt.experiment.__name__ == 'qrt.experiment'
assert 'mlflow' not in sys.modules
"""
    subprocess.run([sys.executable, "-c", code], check=True)


def test_mlflow_tracker_uses_native_tracking_entities(tmp_path, monkeypatch):
    pytest.importorskip("mlflow")
    monkeypatch.setenv("MLFLOW_ALLOW_FILE_STORE", "true")
    tracker = q.experiment.MLflowTracker(
        experiment="qrt-tests",
        tracking_uri=(tmp_path / "mlruns").as_uri(),
    )
    artifact = tmp_path / "model.json"
    artifact.write_text('{"kind": "test"}')

    with tracker.run("filing-extractor", tags={"qrt.domain": "ai"}) as run:
        run.log_params(model="test/model", schema="risk-v1")
        run.log_metrics(validity=1.0, cost=0.02)
        run.log_dataset("filings", fingerprint="sha256:data")
        run.log_model("extractor", artifact=artifact, flavor="pydantic")

    stored = tracker.backend_client.get_run(run.run_id)
    assert stored.info.status == "FINISHED"
    assert stored.data.params["model"] == "test/model"
    assert stored.data.metrics["validity"] == 1.0
    assert stored.data.tags["qrt.domain"] == "ai"
    artifacts = tracker.backend_client.list_artifacts(run.run_id)
    assert {item.path for item in artifacts} == {"datasets", "models"}


def test_mlflow_tracker_requires_an_explicit_or_environment_uri(monkeypatch):
    monkeypatch.delenv("MLFLOW_TRACKING_URI", raising=False)

    with pytest.raises(ValueError, match="requires tracking_uri"):
        q.experiment.MLflowTracker(experiment="research")