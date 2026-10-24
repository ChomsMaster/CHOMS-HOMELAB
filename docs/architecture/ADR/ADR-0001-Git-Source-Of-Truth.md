# ADR-0001 — Git Is the Source of Truth

## Status

Accepted

## Context

Stacks were initially created directly under `/data/docker/stacks`.

That made runtime files drift away from Git and caused unclear ownership.

## Decision

The Git repository is the Single Source of Truth.

Stacks must be edited in:

    /data/projects/choms-homelab/stacks

Runtime is generated into:

    /data/docker/stacks

## Consequences

- Runtime files are not authoritative.
- `.env` files remain runtime-specific.
- Deployments must use `choms deploy <stack>`.
