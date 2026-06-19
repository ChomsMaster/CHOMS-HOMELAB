# ADR-005 - PostgreSQL

## Status

Accepted

## Decision

PostgreSQL will only listen locally through Docker.

## Rationale

- Security
- Reduced attack surface

## Consequences

Database access will always be mediated by applications.
