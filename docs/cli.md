# CLI reference

Every verb prints JSON to stdout and returns exit code 0 when healthy, 1 on
warn or fail. Pipe output to `jq` to build your own checks on top.

## Verbs

| Verb | What it does | Exit code |
| --- | --- | --- |
| `smoke` | Deterministic local check: version and registry, no network calls | 0 if all checks pass |
| `status [--write]` | Probe every subsystem, return a JSON snapshot with one aggregate verdict | 0 if `overall` is ok |
| `list` | Print every registered subsystem with its declared probes and dependencies | 0 |
| `probe --name <subsystem>` | Run one subsystem's probe | 0 if ok |
| `audit` | Full audit, writes `audit-*.json` under the state directory, best-effort proof bind | 0 if `overall` is not fail |
| `boot [--max-wait-s N] [--no-stop-on-critical-fail]` | Cold-boot all subsystems in topological dependency order | 0 if no critical aborts |
| `recover [--flows ...] [--dry-run]` | Repair flows (see below) | 0 if all steps ok |
| `version` | Print the installed version | 0 |

## Probes

Each subsystem declares at most one probe kind. The most authoritative
available probe runs automatically:

| Probe | Used when | Backed by |
| --- | --- | --- |
| HTTP | `http_health=(port, path)` is set | Raw stdlib socket, no HTTP library needed |
| Heartbeat | `heartbeat_path` is set | File mtime compared to `heartbeat_max_age_s` |
| launchd | Only `launchd_label` is set | `launchctl list` parsing (macOS) |

A 401 from an HTTP probe counts as alive: an auth gate answering is a live
service. A 200 with health JSON is the best signal.

## Recovery flows

`recover --flows` accepts a comma-separated list:

- `restart_dead_daemons`: kickstart each launchd-managed subsystem that probes dead.
- `replay_blocked_queue`: reset stuck queue jobs to `queued`, close synthetic
  backfill jobs for nodes that will never run, and refuse to overwrite a live
  proof store with a smaller backup.
- `restore_proof_store_from_backup`: restore the proof store from the newest
  backup when the live store is missing or unusable.

Always preview with `--dry-run` first.

## Configuration

| Variable | Effect | Default |
| --- | --- | --- |
| `RIG_REPO_ROOT` | Override the install root the registry resolves paths against | Walks up looking for a `CLAUDE.md` marker, then the user's home directory |
| `RIG_STATE_DIR` | Override the state directory | `<root>/.omx/state/rig-sovereign` |
| `RIG_TEST_BYPASS_AUTH` | Bypass dashboard auth in tests only | unset (never set this in production) |

```bash
RIG_REPO_ROOT=/opt/my-rig rig-mesh status
RIG_STATE_DIR=/var/lib/rig-state rig-mesh probe --name idle-queue
```

## The default registry

The package ships 17 subsystem declarations covering the layers a local AI
stack usually has: a proof store, queue runner, healer and monitor daemons,
several dashboards, a model router, and backup and retention runners. See
`default_registry()` in `src/rig_mesh/subsystems.py` for the exact list and
probe configuration.

## Extending

Permanent additions go in `default_registry()`. One-off registries are built
programmatically:

```python
from rig_mesh import RigMaster, Subsystem, SubsystemRegistry, default_registry

reg = default_registry()
reg.register(Subsystem(
    name="my-private-llm",
    description="Internal fine-tuned 70B server",
    kind="service",
    http_health=(9100, "/v1/health"),
    depends_on=["proof-store"],
    critical=True,
))

master = RigMaster(reg)
print(master.status_snapshot())
```

A subsystem needs five things: a name, a one-line description, a kind
(`daemon`, `service`, `library`, or `gate`), one probe declaration, and any
`depends_on` names. Mark it `critical=True` when a boot should abort if it is
down.

## Use cases

**Verify the routing path before sending traffic.** Probe the queue daemon,
the model router, and the proof store in order. All three ok means work can be
dispatched.

**Watch a fleet of models.**

```bash
watch -n 30 "rig-mesh status | jq '.probes[] | {name, status}'"
```

**Auto-restart dead daemons.**

```cron
*/5 * * * * /usr/local/bin/rig-mesh recover --flows restart_dead_daemons
```

**One-line health gate in CI.**

```yaml
- name: Health gate
  run: rig-mesh audit && rig-mesh status
```
