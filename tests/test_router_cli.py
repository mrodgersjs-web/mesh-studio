"""Tests for rig_mesh.router and rig_mesh.cli."""
from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

import rig_mesh.cli as cli_mod
from rig_mesh.cli import main as cli_main
from rig_mesh.master import RigMaster
from rig_mesh.router import CommandRouter
from rig_mesh.subsystems import Subsystem, SubsystemRegistry




def _assert_cli_parse_error_json(capsys, monkeypatch, argv: list[str]) -> dict:
    constructed = False

    def fail_router():
        nonlocal constructed
        constructed = True
        raise AssertionError("CommandRouter should not be constructed on parse errors")

    monkeypatch.setattr(cli_mod, "CommandRouter", fail_router)
    with pytest.raises(SystemExit) as e:
        cli_main(argv)
    captured = capsys.readouterr()
    assert e.value.code == 2
    assert captured.out == ""
    payload = json.loads(captured.err)
    assert payload["ok"] is False
    assert payload["error"]
    assert payload["usage"].startswith("usage: rig-master")
    assert constructed is False
    return payload

def _build_router(tmp_path: Path) -> CommandRouter:
    reg = SubsystemRegistry()
    hb = tmp_path / "h.json"
    hb.write_text("{}")
    reg.register(Subsystem(name="x", description="x", kind="daemon", heartbeat_path=hb))
    return CommandRouter(RigMaster(reg))


def test_router_known_verbs(tmp_path: Path):
    r = _build_router(tmp_path)
    verbs = r.known_verbs()
    assert "status" in verbs
    assert "audit" in verbs
    assert "boot" in verbs
    assert "version" in verbs


def test_router_dispatch_unknown_verb(tmp_path: Path):
    r = _build_router(tmp_path)
    out = r.dispatch("does-not-exist")
    assert out["ok"] is False
    assert "unknown verb" in out["error"]


def test_router_status(tmp_path: Path):
    r = _build_router(tmp_path)
    out = r.dispatch("status")
    assert out["ok"] is True
    assert out["verb"] == "status"
    assert "probes" in out and len(out["probes"]) == 1


def test_router_list(tmp_path: Path):
    r = _build_router(tmp_path)
    out = r.dispatch("list")
    assert out["ok"] is True
    assert out["subsystems"][0]["name"] == "x"


def test_router_probe_known(tmp_path: Path):
    r = _build_router(tmp_path)
    out = r.dispatch("probe", {"name": "x"})
    assert out["ok"] is True
    assert out["status"] == "live_ok"


def test_router_probe_unknown(tmp_path: Path):
    r = _build_router(tmp_path)
    out = r.dispatch("probe", {"name": "nope"})
    assert out["ok"] is False
    assert "unknown subsystem" in out["error"]


def test_router_version(tmp_path: Path):
    r = _build_router(tmp_path)
    out = r.dispatch("version")
    assert out["ok"] is True
    assert "rig_master" in out


def test_router_handles_handler_exception(tmp_path: Path, monkeypatch):
    """If a handler raises, dispatch returns ok=False rather than propagating."""
    r = _build_router(tmp_path)
    def boom(args):  # noqa: ANN001
        raise RuntimeError("boom")
    monkeypatch.setattr(r, "_verb_status", boom)
    out = r.dispatch("status")
    assert out["ok"] is False
    assert "boom" in out["error"]


# ---------------------------------------------------------------------------
# CLI smoke

def test_cli_version_exits_0(capsys):
    rc = cli_main(["version"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["ok"] is True
    assert payload["rig_master"]


def test_cli_help_exits_0_human_readable(capsys):
    with pytest.raises(SystemExit) as e:
        cli_main(["--help"])
    captured = capsys.readouterr()
    assert e.value.code == 0
    assert captured.out.startswith("usage: rig-master")
    assert captured.err == ""


def test_cli_root_missing_command_parse_error_json(capsys, monkeypatch):
    payload = _assert_cli_parse_error_json(capsys, monkeypatch, [])
    assert "required" in payload["error"]


def test_cli_unknown_verb_parse_error_json(capsys, monkeypatch):
    payload = _assert_cli_parse_error_json(capsys, monkeypatch, ["nope"])
    assert "invalid choice" in payload["error"]


def test_cli_probe_with_missing_name_parse_error_json(capsys, monkeypatch):
    payload = _assert_cli_parse_error_json(capsys, monkeypatch, ["probe"])
    assert "--name" in payload["error"]


def test_cli_boot_invalid_numeric_arg_parse_error_json(capsys, monkeypatch):
    payload = _assert_cli_parse_error_json(capsys, monkeypatch, ["boot", "--max-wait-s", "not-a-number"])
    assert "invalid float value" in payload["error"]


def test_cli_unknown_option_parse_error_json(capsys, monkeypatch):
    payload = _assert_cli_parse_error_json(capsys, monkeypatch, ["version", "--wat"])
    assert "unrecognized arguments" in payload["error"]
