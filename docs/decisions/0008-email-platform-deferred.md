# ADR 0008: Email platform work is deferred

- **Status:** accepted

## Context

Operating public email requires coordinated network reachability, DNS,
deliverability, abuse prevention, monitoring, backup, and rollback. That scope
is separate from current workload hardening and has not been authorized.

## Decision

Defer mail-server deployment and all related DNS, routing, and provider changes
until explicitly authorized as a dedicated architecture and implementation
task.

## Consequences

No future task may infer permission to deploy email infrastructure or change
mail-related DNS/router state. When resumed, the work must begin with current
external-state verification and a reviewed design.

## Evidence

- [`ROADMAP.md`](../context/ROADMAP.md)
- [`AGENTS.md`](../../AGENTS.md)
