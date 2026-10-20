"""The runnable example in examples/ is executed here so it cannot rot."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "custom_registry.py"


def test_example_module_builds_expected_registry(tmp_path):
    sys.path.insert(0, str(EXAMPLE.parent))
    try:
        module = runpy.run_path(str(EXAMPLE))
    finally:
        sys.path.pop(0)
    reg = module["build_registry"](tmp_path / "worker-heartbeat.json")
    assert [s.name for s in reg.all()] == ["my-queue-runner", "my-model-router"]


def test_example_main_exits_zero(capsys):
    sys.path.insert(0, str(EXAMPLE.parent))
    try:
        module = runpy.run_path(str(EXAMPLE))
        rc = module["main"]()
    finally:
        sys.path.pop(0)
    out = capsys.readouterr().out
    assert rc == 0
    assert '"my-queue-runner"' in out
    assert '"my-model-router"' in out
