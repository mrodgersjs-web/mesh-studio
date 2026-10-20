# Architecture

mesh-studio is a small control plane over a group of local services. It never
runs models or schedules jobs itself; it observes, starts, and repairs the
services that do.

## Layers

```
CLI / MCP / dashboard        thin surfaces, one JSON contract
        |
CommandRouter                verb string + args dict -> RigMaster call
        |
RigMaster                    status snapshot, audit, boot, recovery
        |
SubsystemRegistry            named Subsystem declarations, dependency order
        |
Subsystem.probe()            HTTP / heartbeat / launchd probe -> ProbeResult
```

## Design decisions

**stdlib core.** The HTTP probe speaks raw `socket` so the core package has no
dependencies. FastAPI and uvicorn are opt-in behind the `dashboard` extra; the
MCP server is opt-in behind the `mcp` extra. Importing `rig_mesh` works in any
environment because module attributes resolve lazily.

**Declarative subsystems.** A `Subsystem` is a dataclass: name, description,
kind, one probe declaration, dependency names, and a critical flag. Probes are
picked by authority: HTTP beats heartbeat beats launchd. There is no plugin
discovery or YAML loading; the registry is plain Python so it is greppable and
testable.

**Topological boot.** `SubsystemRegistry.topological_order()` depth-first sorts
by `depends_on` and raises on cycles, so a misconfigured registry fails loudly
instead of half-booting. Boot walks that order, probes after each start, and
aborts when a critical subsystem stays down (configurable with
`--no-stop-on-critical-fail`).

**Truth over claims.** Every verdict is computed from a probe that ran just
now. Heartbeat probes report age in seconds; HTTP probes report the status
code actually received. A 401 counts as alive because an answering auth gate
is a working service.

**Recovery is previewable.** Every recovery flow supports `--dry-run` and
returns a step-by-step report. The queue replay flow refuses to overwrite a
live proof store with a smaller backup, because losing records is worse than
staying stuck.

**One JSON contract.** The CLI, the dashboard API, and the MCP tools all route
through `CommandRouter.dispatch()` and return the same dicts. Adding a verb
means adding one `_verb_<name>` method and, if needed, one argparse
subcommand.

## State and artifacts

The registry resolves two paths at import time, both overridable by
environment variable (`RIG_REPO_ROOT`, `RIG_STATE_DIR`). Audits write
timestamped JSON artifacts under `<state>/rig-master/`, and recovery logs land
under `<state>/rig-master/recovery/`. Nothing is written outside those
directories.

## Testing strategy

The test suite runs offline: probes are exercised against temp heartbeat
files, refused TCP connections, and stubbed `launchctl` output rather than a
live fleet. The dashboard tests use FastAPI's TestClient with an explicit auth
bypass env var, and the MCP tests exercise the tool surface against a temp
registry. `tests/test_examples.py` executes the runnable example in
`examples/` so it cannot rot.
