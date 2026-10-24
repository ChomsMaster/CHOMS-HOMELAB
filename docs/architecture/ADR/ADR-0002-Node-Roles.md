# ADR-0002 — Node Roles

## Status

Accepted

## Decision

CHOMS uses role-based nodes:

- Edge
- Application
- Storage
- Future: Compute

## Consequences

Services are placed by responsibility, not randomly by host.

This enables future scaling by adding nodes.
