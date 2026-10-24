# Security Policy

## Supported Scope

This security policy applies to the CHOMS-HOMELAB repository and operational scripts.

## Secrets Policy

The repository must never contain:

- real passwords
- `.env` files
- private keys
- WireGuard private keys
- Traefik `acme.json`
- API tokens
- database credentials
- backup encryption keys
- plaintext vault exports

## Local Secrets

Local secrets may exist on the server but must remain outside Git.

Known local-only examples:

- `docker/.env`
- `/root/choms/secrets.env`
- Traefik ACME storage
- Authelia secrets

## Recommended Checks

Before pushing:

```bash
git status
git ls-files | grep -Ei '(\.env|acme\.json|secret|private|\.key|\.pem)' || true
grep -RInE '(PASSWORD|SECRET|TOKEN|PRIVATE KEY|BEGIN RSA|BEGIN OPENSSH)' . --exclude-dir=.git || true
```

Recommended future CI checks:

- gitleaks
- trufflehog
- Docker image vulnerability scan
- Compose validation
- dependency checks

## Incident Response

If a secret is accidentally committed:

1. Rotate the secret immediately.
2. Remove it from the repository.
3. Rewrite history if necessary.
4. Invalidate old credentials.
5. Document the incident privately.
6. Review `.gitignore` and CI checks.

## Public Exposure Policy

Public services may be exposed intentionally.

Administrative services must be protected by Authelia, VPN or equivalent controls.

## Current Status

Phase 1 security baseline is complete.

Phase 2 should add automated security scanning and stronger secret management.
