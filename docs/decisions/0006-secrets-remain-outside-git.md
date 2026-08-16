# ADR 0006: Secret values remain outside Git

- **Status:** accepted

## Context

The platform requires database credentials, application secrets, certificates,
and tokens. Publishing those values would compromise workloads and users.

## Decision

Never store Kubernetes Secret values, credentials, private keys, tokens, user
data, or backup contents in Git. Generate Kubernetes Secrets from an ignored
local environment file. Audits may record Secret object and key-reference names
only when operationally necessary.

## Consequences

Repository bootstrap requires securely provisioned local secret material.
Diagnostics and documentation must redact sensitive values. Secret recovery
requires a separate protected process outside this repository.

## Evidence

- [`BOOTSTRAP.md`](../operations/BOOTSTRAP.md)
- [`secrets.env.example`](../../stacks/kubernetes/secrets/secrets.env.example)
- [`stacks/backup/README.md`](../../stacks/backup/README.md)
