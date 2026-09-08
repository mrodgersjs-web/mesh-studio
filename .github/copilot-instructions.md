# Copilot instructions

## Repository purpose

`mesh-studio` is a deterministic control-plane CLI for declaring, probing, booting, auditing, and recovering AI-infrastructure subsystems. It reports system state but does not run models itself.

## Work map

- `src/rig_mesh/`: Python package, CLI, registry, audit, recovery, and MCP surfaces.
- `tests/`: behavioral and subsystem tests.
- `scripts/`: repository smoke entry point.
- `docs/`: architecture, evaluation, and public-boundary guidance.
- `graft/`: generated context; read when needed and leave unchanged.

## Commands

Bootstrap from the repository root:

```bash
python3 -m pip install -e .
```

Test and smoke:

```bash
bash scripts/smoke.sh
```

Run the deterministic CLI smoke:

```bash
rig-mesh smoke
```

## Editing rules

- Keep model execution outside this control plane.
- Keep Builder, Reviewer, and QA authority separate; no role approves its own output.
- Preserve tests, CodeQL gates, proof paths, and human approval for outward or recovery actions.
- Do not add autonomous merge, publish, schedule, or notification behavior.
- Always run the smoke command before claiming done.
