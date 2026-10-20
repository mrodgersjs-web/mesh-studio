# Security Policy

## Supported versions

| Version | Supported |
| --- | --- |
| 1.1.x | yes |
| 1.0.x | security fixes only |
| < 1.0 | no |

## Supported surfaces
This repository's public `main` branch.

## Reporting
Email **security@rodgersintelligence.com** with:
- affected path / command
- impact
- proof of concept (non-destructive)

Do **not** open a public issue for secrets or exploitable bugs.

## Secrets
- Never commit `.env`, cookies, tokens, private keys, or customer data.
- Rotate any credential that may have been exposed.
- Public boundary: `docs/public-boundary.md`.
