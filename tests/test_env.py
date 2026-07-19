import os

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


def test_get_and_require_handle_missing_values(monkeypatch):
    monkeypatch.delenv("QRT_MISSING_VALUE", raising=False)

    assert q.env.get("QRT_MISSING_VALUE") is None
    assert q.env.get("QRT_MISSING_VALUE", "fallback") == "fallback"
    with pytest.raises(KeyError, match="QRT_MISSING_VALUE"):
        q.env.require("QRT_MISSING_VALUE")


def test_utils_load_env_remains_compatible():
    assert q.utils.load_env is q.env.load