# CHOMS Platforms — Active Roadmap

Status values are `pending`, `in_progress`, `blocked`, `completed`, and
`deferred`. The detailed evidence and risk ranking come from the
[workload audit](../operations/KUBERNETES_WORKLOAD_AUDIT.md).

## In progress

| Work | Status | Closure criteria |
|---|---|---|
| Service-by-service Kubernetes hardening | `in_progress` | Complete the ordered direct-workload sequence with one reviewed change per workload, functional validation, consumer health, and drift zero. |

## Next action exact

| Work | Status | Closure criteria |
|---|---|---|
| Reconcile `metallb-system/DaemonSet/speaker` to the digest already published in the vendored manifest | `pending` | Preflight clean; prove effective imageID matches Git; dry-run and diff affect only speaker; preserve three-node availability during RollingUpdate; verify all speakers Ready, VIP and public routes reachable, no new errors, cluster healthy, and speaker drift zero. Do not combine with other MetalLB resources. |

## High priority

| Work | Status | Closure criteria |
|---|---|---|
| Scrutiny collector hardening | `pending` | Pin the current digest; add only supported probes/resources; minimize privilege and device paths without losing SMART discovery; validate both collectors and server ingestion. |
| Scrutiny server privilege reduction | `pending` | Confirm backup/recovery, narrow host paths and privilege safely, add justified CPU/startup controls, and validate UI plus collector ingestion. |
| Jellyfin device-access design | `pending` | Prove hardware transcoding with non-privileged, narrowly mapped devices; preserve library access and playback; document rollback. |
| Independent/off-site backup copy | `pending` | Produce an encrypted copy outside the live NAS failure domain and complete a documented restore validation. |

## Medium priority

| Work | Status | Closure criteria |
|---|---|---|
| Pin mutable direct images: Home, Authelia, Filebrowser | `pending` | One service per commit; pin the exact running imageID without upgrading; validate routes, auth, storage, consumers, and drift zero. |
| Remaining direct-workload probes and resources | `pending` | Use runtime and historical metrics; add only functional probes and conservative controls; one workload per task. |
| Direct-workload `securityContext` hardening | `pending` | Validate each image entrypoint and persistent-volume permissions; enforce least privilege without breaking startup or storage. |
| NetworkPolicy audit | `pending` | Inventory required ingress/egress flows, identify default-open namespaces, propose staged policies, and test consumers before enforcement. |
| Pod Security audit | `pending` | Classify namespaces and exemptions, document privileged device workloads, and produce an enforceable staged policy. |
| Certificate and SAN audit | `pending` | Compare routes, certificate SANs, renewal health, and ownership without exposing private keys; resolve only reviewed mismatches. |
| Split DNS audit | `pending` | Compare public hostnames, CoreDNS declarations, and internal resolution; document intended differences and validate clients. |
| Helm release hardening | `pending` | Review one locked release at a time through versioned values and atomic Helm flow; do not edit rendered workloads. |
| K3s system workload lifecycle | `pending` | Address CoreDNS, metrics-server, and local-path-provisioner only through a planned K3s configuration/version lifecycle. |

## Improvements and future work

| Work | Status | Closure criteria |
|---|---|---|
| Architecture documentation consolidation | `pending` | Reconcile current Kubernetes architecture with historical Docker documents; mark superseded material and remove contradictions without erasing history. |
| CHOMS Platforms web/portfolio | `pending` | Define scope, ownership, deployment model, security review, tests, and documented release procedure. |
| ShiftCore integration | `pending` | Approve architecture and data/security boundaries before deployment; define manifests, consumers, observability, backup, and rollback. |
| Continuous drift detection and CI policy checks | `pending` | Add read-only scheduled drift checks and CI validation with clear failure semantics and no Secret exposure. |
| Repository/name migration | `pending` | Inventory references to the historical name and prepare a reversible migration plan before renaming paths, repository, or Kubernetes resources. |

## Completed foundations

| Work | Status | Closure criteria/evidence |
|---|---|---|
| Kubernetes backup and recovery automation | `completed` | Versioned automation and successful controlled Nextcloud restore test; `b5b8792`. |
| MariaDB hardening | `completed` | Digest, Recreate, probes, healthy consumer; `2948d31`. |
| Nextcloud secure sharing | `completed` | Reproducible enforced policy and isolated E2E cleanup confirmed; `c16fd81` plus runtime evidence. A detailed historical HTTP transcript was intentionally not retained. |
| Workload audit | `completed` | Full inventory and repeatable read-only script; `3d10730`. |
| Redis hardening | `completed` | Recreate, probes, justified resources, digest, consumers healthy; `fc3df18`. |
| PostgreSQL reconciliation | `completed` | Published digest reconciled and validated; runtime-only, no empty commit. |
| MetalLB controller reconciliation | `completed` | Published digest reconciled; webhook, speakers, VIP, routes, and cluster validated; runtime-only. |

## Deferred

| Work | Status | Closure criteria |
|---|---|---|
| Email platform, MX/SPF/DMARC/PTR, and mail-related router changes | `deferred` | Remains untouched until explicit authorization and a dedicated design covering provider constraints, DNS, deliverability, security, backup, and rollback. |
