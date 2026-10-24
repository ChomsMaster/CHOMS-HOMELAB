# ADR 0003: Pin deployed container images by digest

- **Status:** accepted

## Context

Mutable tags can resolve to different bytes across pulls and nodes. The audit
found direct workloads where Git already contained the effective digest but
runtime still declared a tag.

## Decision

For direct workloads, replace mutable image tags with the exact effective
digest already validated in runtime. Digest reconciliation must not silently
upgrade the artifact. Helm and K3s-managed images follow their supported
versioned workflows.

## Consequences

Deployments become reproducible and image changes become explicit. Operators
must compare the runtime `imageID`, Git reference, and proposed diff before a
rollout. Upgrades remain separate tasks.

## Evidence

- [`KUBERNETES_WORKLOAD_AUDIT.md`](../operations/KUBERNETES_WORKLOAD_AUDIT.md)
- [`metallb-native-v0.15.2.yaml`](../../stacks/kubernetes/metallb/metallb-native-v0.15.2.yaml)
- [`CURRENT_STATE.md`](../context/CURRENT_STATE.md)
