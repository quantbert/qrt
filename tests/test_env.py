import json
import os
import sys
from types import SimpleNamespace

import pytest

import qrt as q


def test_values_reads_without_modifying_environment(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text("QRT_TEST_VALUE=from-file\n")
    monkeypatch.delenv("QRT_TEST_VALUE", raising=False)

    assert q.env.values(path) == {"QRT_TEST_VALUE": "from-file"}
    assert "QRT_TEST_VALUE" not in os.environ


def test_load_preserves_existing_values_unless_override_is_enabled(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text("QRT_TEST_VALUE=from-file\n")
    monkeypatch.setenv("QRT_TEST_VALUE", "existing")

    assert q.env.load(path)
    assert q.env.get("QRT_TEST_VALUE") == "existing"

    assert q.env.load(path, override=True)
    assert q.env.require("QRT_TEST_VALUE") == "from-file"


def test_get_handles_missing_values(monkeypatch):
    monkeypatch.delenv("QRT_MISSING_VALUE", raising=False)

    assert q.env.get("QRT_MISSING_VALUE") is None
    assert q.env.get("QRT_MISSING_VALUE", "fallback") == "fallback"


def test_utils_load_env_remains_compatible():
    assert q.utils.load_env is q.env.load


def test_disk_and_info_are_serializable(tmp_path, monkeypatch):
    monkeypatch.setattr(q.env, "accelerators", lambda: ())

    snapshot = q.env.info(tmp_path)

    assert snapshot.disk.path == tmp_path.resolve()
    assert snapshot.disk.total > 0
    assert snapshot.disk.free >= 0
    assert snapshot.device == "cpu"
    assert snapshot.operating_system.name
    assert json.loads(json.dumps(snapshot.as_dict()))["disk"]["path"] == str(
        tmp_path.resolve()
    )


def test_disk_accepts_a_path_that_does_not_exist(tmp_path):
    destination = tmp_path / "future" / "dataset.parquet"

    storage = q.env.disk(destination)

    assert storage.path == destination.resolve()
    assert storage.total > 0


def test_accelerators_detect_nvidia_and_mps(monkeypatch):
    cuda = SimpleNamespace(
        is_available=lambda: True,
        device_count=lambda: 1,
        get_device_name=lambda index: "Test GPU",
        get_device_properties=lambda index: SimpleNamespace(total_memory=24 * 1024**3),
    )
    mps = SimpleNamespace(is_available=lambda: True)
    xpu = SimpleNamespace(is_available=lambda: False)
    torch = SimpleNamespace(
        cuda=cuda,
        version=SimpleNamespace(hip=None),
        backends=SimpleNamespace(mps=mps),
        xpu=xpu,
    )
    monkeypatch.setitem(sys.modules, "torch", torch)

    detected = q.env.accelerators()

    assert detected == (
        q.env.AcceleratorInfo(
            index=0,
            backend="cuda",
            vendor="NVIDIA",
            name="Test GPU",
            memory_total=24 * 1024**3,
        ),
        q.env.AcceleratorInfo(
            index=0,
            backend="mps",
            vendor="Apple",
            name="Apple Silicon GPU",
        ),
    )


def test_device_uses_cuda_name_for_rocm(monkeypatch):
    rocm = q.env.AcceleratorInfo(
        index=0,
        backend="rocm",
        vendor="AMD",
        name="Test AMD GPU",
    )
    monkeypatch.setattr(q.env, "accelerators", lambda: (rocm,))

    assert q.env.device() == "cuda"


def test_require_returns_environment_variable_or_raises(monkeypatch):
    monkeypatch.setenv("QRT_REQUIRED_VALUE", "configured")
    monkeypatch.delenv("QRT_MISSING_VALUE", raising=False)

    assert q.env.require("QRT_REQUIRED_VALUE") == "configured"
    with pytest.raises(KeyError, match="QRT_MISSING_VALUE"):
        q.env.require("QRT_MISSING_VALUE")


def test_require_validates_environment_requirements_file(tmp_path, monkeypatch):
    requirements = tmp_path / "env_requirements.yml"
    requirements.write_text(
        """\
os: Linux
machine: x86_64
disk:
  path: data
  free: 5 GiB
accelerator:
  backends: [cuda, rocm]
  vendors: [NVIDIA, AMD]
  count: 1
  memory: 8 GiB
env: [MARKET_DATA_API_KEY]
"""
    )
    expected = q.env.EnvironmentInfo(
        operating_system=q.env.OSInfo("Linux", "test", "test", "x86_64"),
        disk=q.env.DiskInfo(tmp_path / "data", 100 * 1024**3, 90 * 1024**3, 10 * 1024**3),
        accelerators=(
            q.env.AcceleratorInfo(0, "cuda", "NVIDIA", "Test GPU", 12 * 1024**3),
        ),
        device="cuda",
    )
    inspected_paths = []
    monkeypatch.setattr(
        q.env,
        "info",
        lambda path: inspected_paths.append(path.resolve()) or expected,
    )
    monkeypatch.setenv("MARKET_DATA_API_KEY", "secret")

    assert q.env.require(requirements) is expected
    assert inspected_paths == [(tmp_path / "data").resolve()]


def test_require_reports_all_unsatisfied_requirements(tmp_path, monkeypatch):
    requirements = tmp_path / "env_requirements.yaml"
    requirements.write_text(
        """\
os: Windows
machine: arm64
disk:
  free: 20 GiB
accelerator:
  backends: [cuda]
  count: 1
env: [MISSING_API_KEY]
"""
    )
    snapshot = q.env.EnvironmentInfo(
        operating_system=q.env.OSInfo("Linux", "test", "test", "x86_64"),
        disk=q.env.DiskInfo(tmp_path, 10 * 1024**3, 5 * 1024**3, 5 * 1024**3),
        accelerators=(),
        device="cpu",
    )
    monkeypatch.setattr(q.env, "info", lambda path: snapshot)
    monkeypatch.delenv("MISSING_API_KEY", raising=False)

    with pytest.raises(q.env.EnvironmentRequirementError) as error:
        q.env.require(str(requirements))

    assert len(error.value.failures) == 5
    assert "OS is" in error.value.failures[0]
    assert "required environment variable(s) not set" in error.value.failures[-1]


def test_require_rejects_unknown_requirement_fields(tmp_path):
    requirements = tmp_path / "env_requirements.yml"
    requirements.write_text("ram: 16 GiB\n")

    with pytest.raises(ValueError, match="Unknown top-level requirement.*ram"):
        q.env.require(requirements)