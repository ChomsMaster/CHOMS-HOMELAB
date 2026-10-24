# ADR-0003 — CHOMS Deploy Engine

## Status

Accepted

## Context

Manual Docker Compose operations do not scale well across nodes and services.

## Decision

Create `choms deploy <stack>`.

The command:

1. Finds the stack in Git.
2. Copies it to runtime.
3. Preserves `.env`.
4. Validates Docker Compose.
5. Runs `docker compose up -d`.

## Current Limitations

- No rollback.
- No remote multi-node execution.
- No audit log.
- No automatic health enforcement beyond Docker healthchecks.
