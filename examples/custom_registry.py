"""Register a custom subsystem and print a status snapshot.

Run directly:  python examples/custom_registry.py
Runs offline:  the custom subsystem probes a heartbeat file this script
creates in a temp directory, so the snapshot always has one live entry.
"""
from __future__ import annotations

import json
import socket
import sys
import tempfile
from pathlib import Path

from rig_mesh import RigMaster, Subsystem, SubsystemRegistry


def free_port() -> int:
    """Ask the OS for a free port; nothing binds it, so a probe to it is refused."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def build_registry(heartbeat: Path) -> SubsystemRegistry:
    heartbeat.write_text('{"processed": 1}\n')
    reg = SubsystemRegistry()
    reg.register(Subsystem(
        name="my-queue-runner",
        description="Example background worker with a heartbeat file.",
        kind="daemon",
        heartbeat_path=heartbeat,
        heartbeat_max_age_s=300,
        critical=True,
    ))
    reg.register(Subsystem(
        name="my-model-router",
        description="Example model router with an HTTP health endpoint.",
        kind="service",
        http_health=(free_port(), "/health"),
        depends_on=["my-queue-runner"],
    ))
    return reg


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        reg = build_registry(Path(tmp) / "worker-heartbeat.json")
        snapshot = RigMaster(reg).status_snapshot()
    print(json.dumps(snapshot, indent=2, sort_keys=True))
    return 0 if snapshot.get("overall") in ("ok", "warn") else 1


if __name__ == "__main__":
    sys.exit(main())
