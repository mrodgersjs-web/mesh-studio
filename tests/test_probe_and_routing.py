"""Edge cases for launchd probes, kickstart, registry ordering, and router dispatch."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from rig_mesh.master import RigMaster
from rig_mesh.router import CommandRouter
from rig_mesh.subsystems import (
    Subsystem,
    SubsystemRegistry,
    _repo_root,
    _state_dir,
)


class _FakeCompleted:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _launchd_sub() -> Subsystem:
    return Subsystem(name="d", description="d", kind="daemon", launchd_label="com.x.d")


def test_launchd_probe_parses_pid(monkeypatch):
    monkeypatch.setattr(
        "rig_mesh.subsystems.subprocess.run",
        lambda *a, **k: _FakeCompleted(0, '"PID" = 123;\n"LastExitStatus" = 0;\n'),
    )
    r = _launchd_sub().probe()
    assert r.ok is True and r.status == "live_ok" and r.pid == 123


def test_launchd_probe_one_shot_last_exit_zero(monkeypatch):
    monkeypatch.setattr(
        "rig_mesh.subsystems.subprocess.run",
        lambda *a, **k: _FakeCompleted(0, '"LastExitStatus" = 0;\n'),
    )
    r = _launchd_sub().probe()
    assert r.ok is True and r.status == "live_ok" and r.pid is None


def test_launchd_probe_no_pid_nonzero_exit_is_down(monkeypatch):
    monkeypatch.setattr(
        "rig_mesh.subsystems.subprocess.run",
        lambda *a, **k: _FakeCompleted(0, '"LastExitStatus" = 1;\n'),
    )
    r = _launchd_sub().probe()
    assert r.ok is False and r.status == "down"


def test_launchd_probe_launchctl_failure_is_down(monkeypatch):
    monkeypatch.setattr(
        "rig_mesh.subsystems.subprocess.run",
        lambda *a, **k: _FakeCompleted(3, "", "Could not find service"),
    )
    r = _launchd_sub().probe()
    assert r.ok is False and r.status == "down"


def test_launchd_probe_subprocess_error_is_unknown(monkeypatch):
    def _boom(*a, **k):
        raise OSError("no launchctl")
    monkeypatch.setattr("rig_mesh.subsystems.subprocess.run", _boom)
    r = _launchd_sub().probe()
    assert r.ok is False and r.status == "unknown"


def test_kickstart_without_label_refuses():
    sub = Subsystem(name="x", description="x", kind="daemon")
    out = sub.kickstart()
    assert out["action"] == "none" and out["ok"] is False


def test_kickstart_runs_launchctl(monkeypatch):
    seen = {}

    def _fake(cmd, **k):
        seen["cmd"] = cmd
        return _FakeCompleted(0, "ok", "")
    monkeypatch.setattr("rig_mesh.subsystems.subprocess.run", _fake)
    out = _launchd_sub().kickstart()
    assert out["action"] == "launchctl_kickstart" and out["ok"] is True
    assert seen["cmd"][0] == "launchctl" and seen["cmd"][-1].endswith("com.x.d")


def test_kickstart_error_is_reported(monkeypatch):
    def _boom(*a, **k):
        raise subprocess.SubprocessError("boom")
    monkeypatch.setattr("rig_mesh.subsystems.subprocess.run", _boom)
    out = _launchd_sub().kickstart()
    assert out["ok"] is False and "boom" in out["detail"]


def test_topological_order_puts_dependencies_first():
    reg = SubsystemRegistry()
    reg.register(Subsystem(name="a", description="a", kind="daemon", depends_on=["b"]))
    reg.register(Subsystem(name="b", description="b", kind="daemon"))
    assert [s.name for s in reg.topological_order()] == ["b", "a"]


def test_topological_order_raises_on_cycle():
    reg = SubsystemRegistry()
    reg.register(Subsystem(name="a", description="a", kind="daemon", depends_on=["b"]))
    reg.register(Subsystem(name="b", description="b", kind="daemon", depends_on=["a"]))
    with pytest.raises(ValueError, match="cycle"):
        reg.topological_order()


def test_repo_root_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("RIG_REPO_ROOT", str(tmp_path))
    assert _repo_root() == tmp_path.resolve()


def test_repo_root_falls_back_to_home(tmp_path, monkeypatch):
    monkeypatch.delenv("RIG_REPO_ROOT", raising=False)
    assert _repo_root() == Path.home()


def test_state_dir_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("RIG_STATE_DIR", str(tmp_path / "state"))
    assert _state_dir(Path("/anywhere")) == (tmp_path / "state").resolve()


def test_router_probe_without_name_errors(tmp_path):
    reg = SubsystemRegistry()
    reg.register(Subsystem(
        name="x", description="x", kind="daemon",
        heartbeat_path=tmp_path / "h.json",
    ))
    (tmp_path / "h.json").write_text("{}")
    r = CommandRouter(RigMaster(reg))
    out = r.dispatch("probe", {})
    assert out["ok"] is False and "error" in out


def test_router_probe_unknown_name_errors(tmp_path):
    reg = SubsystemRegistry()
    reg.register(Subsystem(
        name="x", description="x", kind="daemon",
        heartbeat_path=tmp_path / "h.json",
    ))
    (tmp_path / "h.json").write_text("{}")
    r = CommandRouter(RigMaster(reg))
    out = r.dispatch("probe", {"name": "nope"})
    assert out["ok"] is False and "unknown subsystem" in out["error"]


def test_router_unknown_verb_lists_known():
    r = CommandRouter(RigMaster(SubsystemRegistry()))
    out = r.dispatch("dance")
    assert out["ok"] is False and "status" in out["known"]
