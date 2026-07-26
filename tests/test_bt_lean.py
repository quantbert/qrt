from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
import subprocess

import pytest

import qrt as q
import qrt.bt.lean as lean_adapter


@pytest.fixture(autouse=True)
def _available_docker(monkeypatch):
    monkeypatch.setattr(lean_adapter, "_validate_docker_access", lambda: None)


def _lean_result() -> dict:
    day = 1_704_067_200
    days = [day + offset * 86_400 for offset in range(8)]
    equity = [[timestamp, value, value, value, value] for timestamp, value in zip(
        days,
        [100_000, 101_000, 100_500, 102_000, 103_000, 102_500, 104_000, 105_000],
    )]
    return {
        "algorithmConfiguration": {
            "name": "adapter-test",
            "accountCurrency": "USD",
            "startDate": "2024-01-01T00:00:00Z",
            "endDate": "2024-01-08T00:00:00Z",
            "tradingDaysPerYear": 252,
            "parameters": {},
        },
        "charts": {"Strategy Equity": {"series": {"Equity": {"values": equity}}}},
        "orders": {},
        "statistics": {},
        "runtimeStatistics": {},
        "totalPerformance": {"closedTrades": [], "portfolioStatistics": {}, "tradeStatistics": {}},
    }


def _workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "lean-project"
    workspace.mkdir()
    (workspace / "lean.json").write_text("{}", encoding="utf-8")
    (workspace / "config.json").write_text(
        json.dumps({"algorithm-language": "Python"}),
        encoding="utf-8",
    )
    (workspace / "data").mkdir()
    (workspace / "algorithm.py").write_text("class Algorithm: pass\n", encoding="utf-8")
    return workspace


class _FakeProcess:
    def __init__(
        self,
        command,
        *,
        cwd,
        returncode: int = 0,
        write_result: bool = False,
        **_,
    ) -> None:
        self.command = tuple(command)
        self.cwd = Path(cwd)
        self.returncode = None
        self._final_returncode = returncode
        self._write_result = write_result
        self.stdout = StringIO("LEAN stdout\n")
        self.stderr = StringIO("" if returncode == 0 else "LEAN failed\n")

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        del timeout
        if self._write_result and "--output" in self.command:
            output = Path(self.command[self.command.index("--output") + 1])
            (output / "123.json").write_text(json.dumps(_lean_result()), encoding="utf-8")
            (output / "123-summary.json").write_text("{}", encoding="utf-8")
        self.returncode = self._final_returncode
        return self.returncode

    def terminate(self):
        self.returncode = -15

    def kill(self):
        self.returncode = -9


class _TimeoutProcess(_FakeProcess):
    def __init__(self, command, **kwargs) -> None:
        super().__init__(command, **kwargs)
        self._first_wait = True

    def wait(self, timeout=None):
        if self._first_wait and timeout is not None:
            self._first_wait = False
            raise subprocess.TimeoutExpired(self.command, timeout)
        return super().wait(timeout=timeout)


def test_general_run_executes_inside_workspace(monkeypatch, tmp_path):
    workspace = _workspace(tmp_path)
    observed = {}

    def launch(command, **kwargs):
        observed["process"] = _FakeProcess(command, **kwargs)
        return observed["process"]

    monkeypatch.setattr(lean_adapter.subprocess, "Popen", launch)

    run = q.bt.lean.run("config get engine-image", workspace=workspace, executable="/bin/echo")
    result = run.wait()

    assert result.succeeded
    assert result.stdout == "LEAN stdout\n"
    assert observed["process"].cwd == workspace.resolve()
    assert result.specification.command[-3:] == ("config", "get", "engine-image")
    assert json.loads(result.specification.to_json())["workspace"] == str(workspace.resolve())


def test_backtest_owns_exact_output_and_generates_report(monkeypatch, tmp_path):
    workspace = _workspace(tmp_path)
    observed = {}

    def launch(command, **kwargs):
        observed["process"] = _FakeProcess(command, write_result=True, **kwargs)
        return observed["process"]

    monkeypatch.setattr(lean_adapter.subprocess, "Popen", launch)

    run = q.bt.lean.backtest(
        workspace=workspace,
        algorithm="algorithm.py",
        parameters={"backtest-start": "2024-01-02", "count": 10, "enabled": True},
        update_image=False,
        executable="/bin/echo",
    )
    result = run.wait()
    report_path = tmp_path / "report.html"
    report = result.report(report_path, title="Adapter report")

    command = observed["process"].command
    assert result.succeeded
    assert result.result_path == result.output_directory / "123.json"
    assert result.result_path in result.artifacts
    assert result.algorithm == (workspace / "algorithm.py").resolve()
    assert result.output_directory.parent == workspace / "backtests"
    assert "--no-update" in command
    assert ("--parameter", "count", "10") == command[command.index("--parameter", 5) + 3:][:3]
    assert "true" in command
    assert report.title == "Adapter report"
    assert report_path.is_file()


def test_backtest_command_failure_is_typed(monkeypatch, tmp_path):
    workspace = _workspace(tmp_path)
    monkeypatch.setattr(
        lean_adapter.subprocess,
        "Popen",
        lambda command, **kwargs: _FakeProcess(command, returncode=2, **kwargs),
    )

    run = q.bt.lean.backtest(
        workspace=workspace,
        algorithm="algorithm.py",
        executable="/bin/echo",
    )

    with pytest.raises(q.bt.lean.LeanCommandError) as caught:
        run.wait()
    assert caught.value.result.state is q.bt.lean.LeanRunState.FAILED
    assert "LEAN failed" in str(caught.value)


def test_init_creates_workspace_and_constructs_command(monkeypatch, tmp_path):
    workspace = tmp_path / "new-workspace"
    observed = {}

    def launch(command, **kwargs):
        observed["process"] = _FakeProcess(command, **kwargs)
        return observed["process"]

    monkeypatch.setattr(lean_adapter.subprocess, "Popen", launch)

    result = q.bt.lean.init(
        workspace=workspace,
        organization="example",
        language="python",
        executable="/bin/echo",
    )

    assert result.succeeded
    assert workspace.is_dir()
    assert observed["process"].cwd == workspace.resolve()
    assert observed["process"].command[-5:] == (
        "init",
        "--organization",
        "example",
        "--language",
        "python",
    )


def test_backtest_validates_workspace_before_launch(tmp_path):
    workspace = tmp_path / "empty"
    workspace.mkdir()

    with pytest.raises(q.bt.lean.LeanValidationError, match="workspace is not ready"):
        q.bt.lean.backtest(
            workspace=workspace,
            algorithm="missing.py",
            executable="/bin/echo",
        )


def test_backtest_reports_unwritable_output_root(monkeypatch, tmp_path):
    workspace = _workspace(tmp_path)

    def deny(_):
        raise q.bt.lean.LeanValidationError("Backtest output root is not writable")

    monkeypatch.setattr(lean_adapter, "_prepare_output_root", deny)

    with pytest.raises(q.bt.lean.LeanValidationError, match="not writable"):
        q.bt.lean.backtest(
            workspace=workspace,
            algorithm="algorithm.py",
            executable="/bin/echo",
        )


def test_backtest_reports_docker_access_problem(monkeypatch, tmp_path):
    workspace = _workspace(tmp_path)

    def deny():
        raise q.bt.lean.LeanValidationError("Docker is not accessible")

    monkeypatch.setattr(lean_adapter, "_validate_docker_access", deny)

    with pytest.raises(q.bt.lean.LeanValidationError, match="Docker is not accessible"):
        q.bt.lean.backtest(
            workspace=workspace,
            algorithm="algorithm.py",
            executable="/bin/echo",
        )


def test_general_run_rejects_leading_lean(tmp_path):
    with pytest.raises(q.bt.lean.LeanValidationError, match="arguments after 'lean'"):
        q.bt.lean.run("lean --version", workspace=tmp_path, executable="/bin/echo")


def test_wait_timeout_terminates_process(monkeypatch, tmp_path):
    monkeypatch.setattr(
        lean_adapter.subprocess,
        "Popen",
        lambda command, **kwargs: _TimeoutProcess(command, **kwargs),
    )
    run = q.bt.lean.run("--version", workspace=tmp_path, executable="/bin/echo")

    with pytest.raises(q.bt.lean.LeanTimeoutError) as caught:
        run.wait(timeout=0.01)

    assert caught.value.result.state is q.bt.lean.LeanRunState.TIMED_OUT
