# CHOMS Platforms — Current State

This file describes the current operational state, not the full project
history. Historical Docker-era documents remain useful background but are not
the deployment authority for the Kubernetes platform.

## Evidence baseline

- Observed: 2026-08-17 (Europe/Madrid).
- Git baseline: `4a801d1cded3254c41316e385605b84ed8b4d124` on `main`.
- At observation time: clean tree, `HEAD == origin/main`, divergence `0/0`.
- Runtime: three K3s nodes Ready; no failed or pending Pods.
- Detailed inventory: [Kubernetes workload audit](../operations/KUBERNETES_WORKLOAD_AUDIT.md).

Repository visibility could not be confirmed during this update. This context
therefore omits public IP addresses, administrative endpoints, user details,
Secret values, and unnecessary internal topology.

## Architecture

CHOMS Platforms is a three-node K3s platform. MetalLB provides an L2 edge
address, Traefik implements Gateway API ingress, cert-manager manages TLS, and
CoreDNS provides split DNS. Persistent application data is supplied by an NFS
provisioner backed by a dedicated NAS.

The main service groups are:

- Applications: CHOMS Controller, home site, Nextcloud, Portainer, Uptime Kuma.
- Data: MariaDB, PostgreSQL, Redis.
- Identity and edge: Authelia, Traefik, MetalLB, cert-manager.
- Media and utilities: Jellyfin, Threadfin, Filebrowser, qBittorrent.
- Observability: Prometheus, Alertmanager, Grafana, Loki, Alloy, Scrutiny.

Runtime namespaces include `apps`, `databases`, `security`, `traefik`,
`metallb-system`, `cert-manager`, `monitoring`, `logging`, `media`,
`filebrowser`, `qbittorrent`, and `nfs-provisioner`, plus Kubernetes system
namespaces.

Public routes under `chomsmaster.com` are declared in
[`httproutes.yaml`](../../stacks/kubernetes/routes/httproutes.yaml). They cover
the main site, identity, Nextcloud, controller, observability, media, and
operational applications. Do not infer authorization requirements from a
hostname; inspect the route and ForwardAuth policy.

## Declarative ownership

Git is the desired-state source of truth:

- Direct resources live under [`stacks/kubernetes/`](../../stacks/kubernetes/).
- MetalLB uses a vendored native manifest and a separate address-pool file.
- Six releases use locked charts and versioned values: cert-manager, Traefik,
  NFS provisioner, monitoring, Loki, and Alloy.
- Helm changes must use the locked flow documented in
  [`stacks/kubernetes/helm/README.md`](../../stacks/kubernetes/helm/README.md).
- K3s system workloads are managed through the K3s lifecycle, not patched ad
  hoc.
- Secret values are generated from an ignored local environment file and are
  never stored in Git.

The 2026-08-16 audit attributed all 35 active workloads: 17 direct, 15 Helm,
and 3 K3s-managed. No orphan workload or missing direct manifest was found.

## Storage and recovery

All observed PVCs are Bound. Application and database PVCs use NFS-backed
storage; some hardware-oriented workloads intentionally use host paths and
require separate security design.

The versioned recovery system under [`stacks/backup/`](../../stacks/backup/)
provides:

- Kubernetes resource inventory excluding Secret objects.
- Logical backups for MariaDB, PostgreSQL, and Redis.
- Nextcloud consistent snapshots and database dumps.
- NAS synchronization, checksums, GFS retention, and controlled restore tests.

Kubernetes and Nextcloud backup services most recently reported success during
the 2026-08-17 observation. The last documented Nextcloud restore validation
completed on 2026-08-14. Snapshots on the live NAS filesystem do not protect
against total NAS loss; an encrypted independent or off-site copy remains a
known gap. See [`stacks/backup/README.md`](../../stacks/backup/README.md).

## Databases

MariaDB, PostgreSQL, and Redis each run as one Ready replica with zero observed
restarts, a persistent PVC, immutable image digest, health probes, and
`Recreate` rollout strategy.

- MariaDB hardening is published in `2948d31`.
- Redis hardening is published in `fc3df18`.
- PostgreSQL's published digest was reconciled to runtime and validated on
  2026-08-16 without a new commit because Git already contained the solution.

Do not change a single-replica database with shared persistent storage back to
`RollingUpdate`.

## Nextcloud

Nextcloud 31.0.14 is installed, outside maintenance mode, and has no pending
database upgrade. Its application and storage-preparation images are pinned to
the effective digests, and the Deployment uses `Recreate` with one replica.

Public client sharing is the approved external file-delivery mechanism. The
current policy enables public links, requires passwords, applies and enforces
a seven-day expiration, and disables public upload. The policy is reproducible
through an idempotent script and is documented in
[`NEXTCLOUD_SHARING.md`](../operations/NEXTCLOUD_SHARING.md).

An isolated E2E sharing exercise preceded the workload audit. The durable audit
evidence confirms zero residual temporary users, shares, files, or Secrets, and
current runtime confirms the enforced policy. The repository does not retain
credentials, tokens, or a detailed HTTP assertion transcript, so those
historical request-level results cannot be independently replayed from Git.
SMB, NFS, and the NAS must not be exposed publicly for client delivery.

## Security and observability

Authelia protects selected routes through ForwardAuth. Prometheus, Grafana,
Loki, Alloy, Uptime Kuma, and Scrutiny provide metrics, logs, availability, and
disk-health visibility. The platform certificate was Ready at observation.

Strong security contexts already exist for several control-plane workloads,
but the audit identifies intentional privileged device access in Jellyfin and
Scrutiny, missing controls in the Scrutiny collectors, mutable images, and
incomplete resource/probe coverage. These require per-image testing rather
than blanket UID or capability changes.

Prometheus is protected by the existing Authelia ForwardAuth pattern through a
Middleware scoped to `monitoring` and a `one_factor` access-control rule.
Anonymous requests redirect once to Authelia without a loop. The change did not
alter the Helm-managed Prometheus workload: its internal readiness, 24 active
targets, zero down targets, Grafana health, storage, and effective images
remained intact during the 2026-08-17 validation.

The non-mutating 2026-08-17 security baseline found no established Critical
risk. It confirmed that the Prometheus query interface is anonymously
reachable and has no ForwardAuth filter in Git, no NetworkPolicy is versioned,
most direct workloads retain default ServiceAccount-token and security-context
behavior, and backup/restore maturity is uneven outside Nextcloud and the
databases. The audit environment could not access `kubectl` or Helm, so current
runtime-only RBAC, target, event, restart, and effective-image checks remain
explicitly pending rather than inferred. See the
[security baseline](../audits/KUBERNETES_SECURITY_BASELINE_2026-08-17.md) and
[hardening backlog](../audits/HARDENING_BACKLOG.md).

The 2026-08-17 read-only IAM and observability audit completed the previously
missing runtime evidence. Portainer has an unversioned `cluster-admin` binding;
14 direct workloads use `default` ServiceAccounts with projected tokens and no
demonstrated API need; Alloy, Grafana, Loki, and kube-state-metrics have
reducible Secret-read scope. Prometheus has 24/24 active targets through ten
ServiceMonitors, with no PodMonitor, Probe, or additional scrape configuration.
See the [IAM and observability audit](../audits/KUBERNETES_IAM_OBSERVABILITY_AUDIT_2026-08-17.md).

A focused read-only Portainer diagnosis found no retained evidence that its
write, Secret, exec, RBAC, impersonation, token, node, storage, CRD, or webhook
authority has been used. Audit logs and attributable managed fields are not
available, so historical use cannot be excluded. Portainer is exposed through
its native authentication without Authelia ForwardAuth. A Secret-free viewer
is the provisional minimum profile; the Platform owner must still identify any
required mutation, resource kind, namespace, logs, or exec workflow before an
RBAC change. See the [Portainer IAM diagnosis](../audits/PORTAINER_IAM_001_DIAGNOSIS_2026-08-17.md).

## Completed operational blocks

- Backup and recovery automation, including a documented restore validation.
- MariaDB rollout and health hardening.
- Nextcloud image reconciliation.
- Secure, reproducible Nextcloud public-sharing policy.
- Isolated E2E public-sharing exercise with cleanup confirmed; detailed
  request-level evidence was not retained.
- Complete Kubernetes workload audit and read-only audit script.
- Redis rollout, probe, resource, and digest hardening.
- PostgreSQL digest reconciliation and consumer validation.
- MetalLB controller digest reconciliation and VIP/webhook validation.
- Non-mutating Kubernetes security, resilience, and maintainability baseline
  with a one-block-at-a-time hardening backlog.
- Prometheus HTTPRoute protection with namespaced Authelia ForwardAuth,
  validated without changing the Prometheus workload or its consumers.
- Read-only IAM, effective-RBAC, and Prometheus discovery audit covering all
  managed workloads and active targets.
- Read-only Portainer IAM-001 diagnosis with three candidate access profiles;
  no authorization change was made.

The last three runtime-only reconciliations created no empty commits when Git
already contained the correct desired state.

## Current risks

- MetalLB speaker still declares its version tag at runtime while Git already
  contains the matching digest. A reconciliation attempt on 2026-08-17 was
  rolled back after all three new speakers repeatedly failed memberlist joins.
  TCP/7946 was reachable locally on the control-plane node but blocked or
  unreachable from that node to both workers. Two speakers also encountered an
  immutable-node conflict updating the existing `ServiceL2Status`. The VIP and
  public routes remained available, but digest reconciliation is blocked until
  node-to-node memberlist connectivity and L2 status ownership are understood.
- Speaker `/metrics` passes native kubelet readiness/liveness checks but was not
  reachable through cross-node, API proxy, or temporary port-forward tests;
  Prometheus had no matching active `speaker` target in the checked query.
- No NetworkPolicy is versioned, and effective runtime east-west isolation
  still requires a fresh authorized inventory.
- Portainer receives unversioned `cluster-admin`; no privileged workflow is
  demonstrated, while the public route relies on native authentication rather
  than Authelia. Owner scope is required before replacing the binding.
- Alloy, Grafana, Loki, and kube-state-metrics can read Secret metadata more
  broadly than their current consumers require.
- Scrutiny collectors and server, and Jellyfin, have broad device/host access.
- Home, Authelia, Filebrowser, and the Scrutiny collector use mutable tags.
- Some direct, Helm, and K3s-managed workloads lack complete probes or resource
  controls.
- Portainer and Uptime Kuma have low-risk registry-prefix drift.
- Home content has non-workload drift that requires a separate content review.
- NetworkPolicies and Pod Security controls have not yet received a dedicated
  platform-wide audit.
- Complete NAS loss is not covered by the current same-filesystem snapshots.
- MetalLB has no metrics ServiceMonitor/PodMonitor. Controller metrics are
  reachable, but only one of three speaker TCP/7472 endpoints was reachable
  from Prometheus; this is separate from the blocked TCP/UDP 7946 memberlist and
  `ServiceL2Status` investigation.

## Operating conventions

Follow [`AGENTS.md`](../../AGENTS.md), the active
[`ROADMAP.md`](ROADMAP.md), and the deployment procedure in
[`DEPLOY.md`](../operations/DEPLOY.md). Work in small reversible blocks, keep
one workload and one logical change per commit, validate consumers, and record
state changes in the operational memory.
