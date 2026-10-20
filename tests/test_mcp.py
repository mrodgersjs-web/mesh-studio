"""Tests for the rig_mesh.mcp_server module.

The MCP surface is tested at the tool-function level, which does not require
the ``mcp`` package to be installed. The ``build_mcp_server()`` function is
tested only for its graceful ImportError behaviour (covered by the optional
import guard).
"""
from __future__ import annotations

import json

import pytest

from rig_mesh.mcp_server import (
    HEALTH_CHECK_PROMPT,
    prompt_health_check,
    resource_registry,
    tool_get_status,
    tool_list_subsystems,
    tool_probe_subsystem,
    tool_run_audit,
    tool_smoke,
)

# ---------------------------------------------------------------------------
# tool_smoke

def test_tool_smoke_ok():
    result = tool_smoke()
    assert result["ok"] is True
    assert result["result"] == "PASS"
    assert result["verb"] == "smoke"


def test_tool_smoke_checks_structure():
    result = tool_smoke()
    checks = result["checks"]
    assert "version_ok" in checks
    assert "registry_populated" in checks
    assert "subsystem_count" in checks


# ---------------------------------------------------------------------------
# tool_list_subsystems

def test_tool_list_subsystems_ok():
    result = tool_list_subsystems()
    assert result["ok"] is True
    assert isinstance(result["subsystems"], list)
    assert len(result["subsystems"]) > 0


def test_tool_list_subsystems_has_required_keys():
    result = tool_list_subsystems()
    first = result["subsystems"][0]
    for key in ("name", "description", "kind"):
        assert key in first, f"missing key: {key}"


# ---------------------------------------------------------------------------
# tool_get_status

def test_tool_get_status_returns_dict():
    result = tool_get_status()
    assert isinstance(result, dict)
    assert "verb" in result
    assert result["verb"] == "status"


def test_tool_get_status_has_overall():
    result = tool_get_status()
    assert "overall" in result
    assert result["overall"] in ("ok", "warn", "fail")


# ---------------------------------------------------------------------------
# tool_probe_subsystem

def test_tool_probe_subsystem_unknown_name():
    result = tool_probe_subsystem("no-such-subsystem-xyz")
    assert result["ok"] is False
    assert "error" in result


def test_tool_probe_subsystem_known_name():
    # 'proof-store' is always registered in the default registry
    result = tool_probe_subsystem("proof-store")
    # Result is either ok or not — just verify structure
    assert "ok" in result
    assert "verb" in result
    assert result["verb"] == "probe"


# ---------------------------------------------------------------------------
# tool_run_audit

def test_tool_run_audit_returns_dict(tmp_path, monkeypatch):
    from rig_mesh import audit as audit_mod
    monkeypatch.setattr(audit_mod, "_REPORT_DIR", tmp_path)
    result = tool_run_audit()
    assert isinstance(result, dict)
    assert "verb" in result
    assert result["verb"] == "audit"


# ---------------------------------------------------------------------------
# resource_registry

def test_resource_registry_is_valid_json():
    raw = resource_registry()
    parsed = json.loads(raw)
    assert "subsystems" in parsed


def test_resource_registry_subsystem_count():
    raw = resource_registry()
    parsed = json.loads(raw)
    assert len(parsed["subsystems"]) > 0


# ---------------------------------------------------------------------------
# resource_audit_latest

def test_resource_audit_latest_missing_returns_error_json(tmp_path, monkeypatch):
    """When no audit artifact exists, returns a JSON error object."""
    from rig_mesh import subsystems as sub_mod
    monkeypatch.setattr(sub_mod, "STATE_DIR", tmp_path)
    # Re-import the resource fn so it picks up the patched STATE_DIR
    from rig_mesh.mcp_server import resource_audit_latest as fn
    raw = fn()
    parsed = json.loads(raw)
    assert "error" in parsed


def test_resource_audit_latest_present(tmp_path, monkeypatch):
    """When an audit artifact exists, it is returned verbatim."""
    from rig_mesh import subsystems as sub_mod
    monkeypatch.setattr(sub_mod, "STATE_DIR", tmp_path)
    master_dir = tmp_path / "rig-master"
    master_dir.mkdir(parents=True)
    artifact = {"audit_id": "audit-test-123", "overall": "ok"}
    (master_dir / "audit-latest.json").write_text(json.dumps(artifact))

    from rig_mesh.mcp_server import resource_audit_latest as fn
    raw = fn()
    parsed = json.loads(raw)
    assert parsed["audit_id"] == "audit-test-123"


# ---------------------------------------------------------------------------
# prompt_health_check

def test_health_check_prompt_contains_snapshot():
    snapshot = {"overall": "ok", "probes": []}
    prompt = prompt_health_check(snapshot)
    assert "ok" in prompt
    assert "critical_alerts" in prompt  # instruction key


def test_health_check_prompt_template_not_empty():
    assert len(HEALTH_CHECK_PROMPT) > 100


def test_health_check_prompt_no_snapshot_calls_get_status():
    """Calling prompt_health_check() with no args should inject a live snapshot."""
    prompt = prompt_health_check()
    # The live snapshot has an 'overall' key — it should appear in the prompt
    assert "overall" in prompt


# ---------------------------------------------------------------------------
# build_mcp_server — ImportError path

def test_build_mcp_server_raises_import_error_when_mcp_missing(monkeypatch):
    """If the mcp package is absent, build_mcp_server raises ImportError."""
    import sys

    # Temporarily hide the mcp package
    original = sys.modules.get("mcp")
    sys.modules["mcp"] = None  # type: ignore[assignment]
    # Also block the submodule path
    for key in list(sys.modules.keys()):
        if key.startswith("mcp."):
            sys.modules[key] = None  # type: ignore[assignment]

    try:
        # We need to re-import with mcp blocked — reload doesn't work cleanly
        # so we patch at the import level instead
        import builtins
        real_import = builtins.__import__

        def blocking_import(name, *args, **kwargs):
            if name == "mcp" or name.startswith("mcp."):
                raise ImportError(f"blocked: {name}")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", blocking_import)

        from rig_mesh.mcp_server import build_mcp_server
        with pytest.raises(ImportError, match="mcp"):
            build_mcp_server()
    finally:
        # Restore
        if original is None:
            sys.modules.pop("mcp", None)
        else:
            sys.modules["mcp"] = original


# ---------------------------------------------------------------------------
# CLI and SSE transport

def test_main_parses_sse_port(monkeypatch):
    from rig_mesh import mcp_server

    called = []

    def fake_serve(use_sse=False, sse_port=8092):
        called.append((use_sse, sse_port))

    monkeypatch.setattr(mcp_server, "serve", fake_serve)
    mcp_server.main(["--sse", "--port", "9000"])
    assert called == [(True, 9000)]


def test_serve_passes_port_to_constructor_and_only_transport_to_run(monkeypatch):
    from rig_mesh import mcp_server

    observed = {}

    class FakeServer:
        def run(self, **kwargs):
            observed["run"] = kwargs

    def fake_build_mcp_server(*, port):
        observed["port"] = port
        return FakeServer()

    monkeypatch.setattr(mcp_server, "build_mcp_server", fake_build_mcp_server)
    mcp_server.serve(use_sse=True, sse_port=9000)
    assert observed == {"port": 9000, "run": {"transport": "sse"}}
