# ADR 0001: Kubernetes is the primary platform

- **Status:** accepted

## Context

CHOMS Platforms operates a three-node K3s cluster with declarative application,
database, edge, storage, security, and observability workloads. Legacy Docker
material remains in the repository as engineering history but no longer
describes the primary deployment model.

## Decision

Use K3s Kubernetes as the primary workload platform. Manage direct workloads
with Kubernetes manifests and selected shared services with locked Helm
releases.

## Consequences

Changes require Kubernetes-aware rollout, health, storage, and consumer
validation. Legacy Docker procedures must not be assumed current. K3s system
components are changed only through a planned K3s lifecycle.

## Evidence

- [`README.md`](../../README.md)
- [`BOOTSTRAP.md`](../operations/BOOTSTRAP.md)
- [`KUBERNETES_WORKLOAD_AUDIT.md`](../operations/KUBERNETES_WORKLOAD_AUDIT.md)
