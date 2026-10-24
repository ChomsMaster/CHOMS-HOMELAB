# ADR 0002: Git is the declarative source of truth

- **Status:** accepted

## Context

Runtime edits are difficult to reproduce and caused observed image drift even
when the effective image bytes matched the repository.

## Decision

Store desired direct manifests, vendored artifacts, locked Helm values, and
reproducible configuration automation in Git. Reconcile runtime from reviewed
versioned sources rather than treating live objects as permanent configuration.

## Consequences

Every operational change requires local validation, server-side dry-run or Helm
rendering, a reviewed runtime diff, rollout validation, and final drift check.
One logical change maps to one commit; runtime-only reconciliation does not
justify an empty commit.

## Evidence

- [`DEPLOY.md`](../operations/DEPLOY.md)
- [`stacks/kubernetes/`](../../stacks/kubernetes/)
- [`KUBERNETES_WORKLOAD_AUDIT.md`](../operations/KUBERNETES_WORKLOAD_AUDIT.md)
