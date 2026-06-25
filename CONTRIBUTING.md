# Contributing

CHOMS-HOMELAB is currently a personal infrastructure project.

Contributions, ideas and reviews are welcome, but changes should follow the project architecture and operational model.

## Principles

- Keep infrastructure reproducible.
- Keep secrets out of Git.
- Prefer modular files over monolithic files.
- Document operational decisions.
- Validate before committing.
- Use Git as the source of truth.

## Before Submitting Changes

Run:

```bash
choms health
choms compose config
git status
```

For documentation-only changes, ensure the docs remain aligned with the current architecture.

## Commit Style

Use clear commit messages:

```text
feat: add new capability
fix: correct broken behavior
docs: update documentation
refactor: reorganize without behavior change
security: improve security posture
```

## Secrets

Never commit:

- `.env`
- `.env.*`
- `acme.json`
- private keys
- passwords
- tokens
- database credentials
- VPN private keys

## Roadmap Alignment

New features should align with the roadmap:

1. Phase 2 — Backups and recovery
2. Phase 3 — Service expansion
3. Phase 4 — Network and security maturity
4. Phase 5 — Cluster and platform engineering
