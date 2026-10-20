# Legacy README (retired)

Superseded by README.md and docs/. Only the closing tail remains; it is removed next.
pytest
```

89 tests covering registry, probes (HTTP refused, heartbeat fresh / stale /
missing, launchd parser, no-probe path), topological sort with cycle
detection, audit aggregation, boot ordering with critical-fail abort, recovery
flows, router dispatch, CLI argparse (including `smoke`), MCP tool surface,
and the FastAPI dashboard (auth-bypass aware). 2 tests skip when the optional
`services.security` auth module isn't installed.

CI runs on every push: pytest on py3.10 / 3.11 / 3.12 + compile lint.
A weekly workflow (`weekly.yml`) additionally runs every Monday and writes a
quality-gate summary — it never deploys or merges automatically.

---

## Design notes

- **stdlib only for the core.** HTTP probes use raw `socket`. FastAPI / uvicorn
  are opt-in via the `[dashboard]` extra.
- **No live LLM.** Every check is deterministic and re-runnable. The optional
  proof binding reaches into a `proof_system` module if installed; otherwise
  degrades silently.
- **Truth-tracker doctrine.** Probes always report what's reachable right now,
  not what a YAML claims. The CLI's exit code reflects live state, never the
  scorecard.
- **macOS-first.** `launchctl bootstrap` / `kickstart` for daemon control.
  Heartbeat + HTTP probes are platform-agnostic, so Linux/systemd users can
  ignore the launchd-only Subsystems and add their own.

---

## License

MIT — see [`LICENSE`](LICENSE).


---



## Video walkthrough

- Script: [`docs/video-script.md`](docs/video-script.md)
- Recording: [`assets/demo.mp4`](assets/demo.mp4) (75s captioned)
- Preview: [`assets/demo.gif`](assets/demo.gif)

![demo preview](assets/demo.gif)

## FDE bar (this studio)

| Practice | Here |
| --- | --- |
| Employer summary | top of README |
| 60s / smoke proof | ......................................                                   [100%]
{
  "ok": true,
  "checked": 7,
  "missing": []
}
{
  "ok": true,
  "failed": 0,
  "results": {
    "robust_madz": {
      "ok": true,
      "verdict": "PASS"
    },
    "surprisal": {
      "ok": true,
      "verdict": "PASS"
    },
    "blend_value": {
      "ok": true,
      "verdict": "PASS"
    },
    "expected_free_energy": {
      "ok": true,
      "verdict": "PASS"
    },
    "composite_sigma": {
      "ok": true,
      "verdict": "PASS"
    },
    "pbt": {
      "ok": true,
      "verdict": "PASS"
    },
    "proof_packet": {
      "ok": true,
      "seal_prefix": "sha256:72103a22618be0c5a"
    },
    "unittest_l10": {
      "ok": true,
      "ran": 38,
      "failures": 0
    }
  }
}
jake-studio smoke PASS |
| Public boundary |  |
| Claim under test | '"rig-mesh smoke PASS"' |
| Related fleet | [profile](https://github.com/mrodgersjs-web) · [resume](https://github.com/mrodgersjs-web/resume) · [patents teaser](https://github.com/mrodgersjs-web/patents) |

If ......................................                                   [100%]
{
  "ok": true,
  "checked": 7,
  "missing": []
}
{
  "ok": true,
  "failed": 0,
  "results": {
    "robust_madz": {
      "ok": true,
      "verdict": "PASS"
    },
    "surprisal": {
      "ok": true,
      "verdict": "PASS"
    },
    "blend_value": {
      "ok": true,
      "verdict": "PASS"
    },
    "expected_free_energy": {
      "ok": true,
      "verdict": "PASS"
    },
    "composite_sigma": {
      "ok": true,
      "verdict": "PASS"
    },
    "pbt": {
      "ok": true,
      "verdict": "PASS"
    },
    "proof_packet": {
      "ok": true,
      "seal_prefix": "sha256:994147477512cf8a6"
    },
    "unittest_l10": {
      "ok": true,
      "ran": 38,
      "failures": 0
    }
  }
}
jake-studio smoke PASS fails, the README claim is considered false until fixed.
