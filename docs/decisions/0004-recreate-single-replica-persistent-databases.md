# ADR 0004: Recreate single-replica persistent databases

- **Status:** accepted

## Context

A RollingUpdate can briefly allow two database Pods to access shared persistent
storage. MariaDB previously exhibited a transient storage-related startup error
during such a rollout. Redis and PostgreSQL also run as single replicas with
persistent PVCs.

## Decision

Use `strategy.type: Recreate` for single-replica database Deployments backed by
persistent storage unless a separately designed clustered database architecture
supports concurrent instances safely.

## Consequences

Routine rollouts include brief database downtime but avoid concurrent writers.
Every rollout requires a validated backup or reconstruction path, startup and
steady-state probes, and consumer validation.

## Evidence

- [`mariadb.yaml`](../../stacks/kubernetes/databases/mariadb.yaml)
- [`postgres.yaml`](../../stacks/kubernetes/databases/postgres.yaml)
- [`redis.yaml`](../../stacks/kubernetes/databases/redis.yaml)
- [`WORKLOG.md`](../context/WORKLOG.md)
