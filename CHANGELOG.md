# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-10-19

### Added
- `tests/test_packaging.py` asserting the package version matches the
  pyproject metadata and the `py.typed` marker ships.
- `examples/custom_registry.py`, a runnable example exercised by
  `tests/test_examples.py`.
- `docs/cli.md` (verbs, probes, recovery flows, configuration, extension)
  and `docs/mcp.md` (tools, resources, prompts).
- `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1), issue templates,
  pull request template, and Dependabot config for pip and GitHub Actions.
- Ruff configuration in `pyproject.toml`; `ruff` and `pytest-cov` in the
  `dev` extra.

### Changed
- README rewritten: single introduction, measured test counts, and depth
  moved to `docs/`.
- `docs/architecture.md` rewritten with design notes taken from the code.
- CI runs ruff and the full pytest suite with coverage on Python 3.10 to
  3.13; the smoke workflow now runs the real tests as well.
- Typing modernized: `Optional[X]` annotations are now `X | None`.
- `RIG_REPO_ROOT` falls back to the user's home directory instead of a
  machine-specific path.
- Security reports go to security@rodgersintelligence.com.

### Fixed
- Removed unused imports across `src/rig_mesh` and the test suite.
- Removed stale repository URLs from `HANDOFF.md`.

## [1.0.0] - 2026-08-04

### Added
- Initial standalone release: subsystem registry, HTTP/heartbeat/launchd
  probes, status snapshot, audit artifacts, topological boot, recovery
  flows, `rig-mesh` CLI, optional FastAPI dashboard, optional MCP server.

[1.1.0]: https://github.com/mrodgersjs-web/mesh-studio/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/mrodgersjs-web/mesh-studio/releases/tag/v1.0.0
