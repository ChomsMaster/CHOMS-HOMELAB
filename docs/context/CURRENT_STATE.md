# CHOMS Platforms — Current State

This file describes the current operational state, not the full project
history. Historical Docker-era documents remain useful background but are not
the deployment authority for the Kubernetes platform.

## Evidence baseline

- Observed: 2026-08-18 (Europe/Madrid).
- Pre-change Git baseline: `174ed36c2f5be6e6387ef15541402571fd09a876`
  on `main`.
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

On 2026-08-25 the Traefik release values were reconciled to the existing live
Gateway, provider, replica, affinity, resource, RBAC and LoadBalancer contract.
The obsolete `cert-manager.io/cluster-issuer` Gateway annotation was removed;
the separate `traefik/choms-platform` Certificate remains the sole declarative
TLS owner and retained Ready revision 6 with `choms-platform-tls`. Traefik
remained 2/2, the Gateway remained Accepted and Programmed, public and
ForwardAuth-protected HTTPS paths passed, and the hostname warning did not
recur after reconciliation.

On 2026-08-27 Alertmanager Telegram delivery was enabled for `critical` alerts
and resolved notifications. `Watchdog`, `warning` and unmatched alerts remain
on the `null` receiver, including the three historical `KubeJobFailed`
warnings. The Alertmanager configuration and bot token live in an external
runtime Secret referenced and mounted by the locked monitoring release; Git
contains only the Secret contract and a reusable interactive creation/rotation
script. A real firing/resolved integration test passed. An initial
`chat not found` response was corrected by reconciling the verified bot/chat
pair without exposing either value. The same bot/chat may later be reused by
the RP3, but the RP3 must manage its own credential copy and lifecycle.

Strong security contexts already exist for several control-plane workloads,
but the audit identifies intentional privileged device access in Jellyfin and
Scrutiny, missing controls in the Scrutiny collectors, mutable images, and
incomplete resource/probe coverage. These require per-image testing rather
than blanket UID or capability changes.

On 2026-08-18 SUP-001 pinned only the Scrutiny collector image to the exact
digest already running on both expected nodes. The DaemonSet RollingUpdate
kept both collectors available, each retained its sanitized two-device count,
startup collection completed twice, and the server accepted two registrations
and four SMART uploads without failed API posts. Probes, resources, privilege,
devices, host paths, the Scrutiny server, route, storage, and network were not
changed. Those separate hardening gaps remain open.

On 2026-08-18 RES-002 moved the Scrutiny collector from BestEffort to bounded
resources using seven days of Prometheus evidence. Per-collector peaks were
5.19–6.24 mCPU, 8.31–10.18 MiB working set and 5.52–6.86 MiB RSS, with zero
OOM events. Requests are now `10m` CPU and `32Mi` memory; limits are `250m`
CPU and `128Mi` memory. No probes were added: the persistent process is cron,
the collector is a six-hour one-shot child, and v0.8.2 exposes no supported
health endpoint or durable state that can distinguish an internal hang without
coupling restarts to disk, network, or server health. `SEC-002` and `SEC-003`
remain pending; image, privilege, devices, host paths, server, storage and
network are unchanged.

On 2026-08-18 SEC-002 tested privilege reduction with temporary, non-uploading
canaries on both collector nodes. The privileged reference read both devices
on each node. A root, non-privileged collector with `SYS_RAWIO`, dropped
capabilities, no privilege escalation and `RuntimeDefault` seccomp discovered
both devices but could not open either one. Removing seccomp and even granting
all capabilities did not change that result, which isolates the blocker to the
containerd device cgroup rather than a missing Linux capability. Kubernetes
rejected individual host block devices through `volumeDevices` because that
API accepts only PVC/Ephemeral block-mode sources. A read-only root filesystem
also failed before startup because the v0.8.2 entrypoint and cron require
writes in the image filesystem. No effective control can be layered on
`privileged: true`: Kubernetes forces all capabilities, privilege escalation,
and unconfined seccomp/AppArmor. The DaemonSet therefore remains unchanged and
SEC-002 is blocked pending a stable device-plugin/CDI or equivalent supported
device-mapping design. `SEC-003` remains pending and untouched.

On 2026-08-19 the documentary review of generic device plugins found no
candidate that simultaneously demonstrates the required security, maintenance
and K3s/containerd compatibility. `squat/generic-device-plugin` is technically
plausible and can allocate explicit Linux devices through the Device Plugin
API, but its published DaemonSet is privileged and mounts the complete `/dev`,
transferring rather than removing the risk. `NVIDIA/k8s-device-plugin` targets
NVIDIA GPUs and does not apply to Scrutiny SATA/SAS devices. Developing a
purpose-built plugin for four disks is not recommended. The current Scrutiny
design is therefore retained and SEC-002 remains `blocked`, with this residual
risk temporarily accepted. A future host-service collector design remains an
alternative requiring a separate architectural decision and work block.
`SEC-003` remains pending and must not be started.

On 2026-08-19 the non-mutating SEC-003 backup prerequisite review found that
Scrutiny `0.8.2` embeds InfluxDB `2.2.0` and has no existing backup coverage.
The protected state is the 28 KiB SQLite configuration database and
approximately 104 MiB of InfluxDB data under the existing server paths. A
direct hot copy of the InfluxDB tree is not considered safe. The design target
is the official InfluxDB backup/restore flow plus a consistent SQLite backup;
the current image does not include the `influx` CLI, so a compatible tool or
authenticated API access through a Secret reference will be needed without
exposing values. Reserve 250 MiB per copy and 1 GiB for an isolated restore;
use RPO 24 hours and RTO 1–2 hours. An isolated restoration is mandatory before
any SEC-003 privilege or hostPath change. No securityContext, hostPath,
device, or server change was made.

On 2026-08-21 a manual cold bootstrap backup closed the recovery prerequisite
needed before any InfluxDB authorization recovery. Only the Scrutiny server was
scaled to zero, for 83 seconds. Its configuration and complete InfluxDB 2.2.0
state were copied from read-only hostPath mounts to a mode-0700 staging tree on
the existing NAS backup export, checked, and atomically published. An isolated
1 GiB restore then passed SQLite integrity and InfluxDB series, TSM, WAL and
tombstone verification before the pinned Scrutiny 0.8.2 image and embedded
InfluxDB started healthy without a Service, route, host port or collector
endpoint. Two initial restore Pods failed before data validation because of
temporary copy-path and ownership-preservation errors; both were removed and
the corrected procedure passed. Production returned to 1/1, collectors stayed
2/2 with recent ingestion, manifests retained drift zero, and no warning
occurred after stabilization. The copy is a sensitive one-time bootstrap, not
the recurring RPO-24-hour solution. No token, Secret, recovery command,
production security context, image, device, hostPath or configuration changed.
`SEC-003` remains pending.

On 2026-08-21 the separate authorization prerequisite was completed with the
official InfluxDB 2.2.0 `influxd recovery auth create-operator` flow. Scrutiny
was stopped for 43 seconds, the pinned server image mounted only its InfluxDB
path in a temporary token-free Pod, and the command output was consumed by a
closed stdin pipeline. The new authorization is stored only in the runtime
Secret `monitoring/scrutiny-backup-influx-operator`, whose contract contains
exactly `token` and `authorization-id`; Git contains neither value. A GET of
the authorization itself returned HTTP 200 with its body discarded. Scrutiny
returned 1/1, collectors remained 2/2 with successful recent collection,
three nodes were Ready, no unhealthy Pod or new Warning remained, and server
plus collector drift was zero. No recurring backup, restore automation,
production image, security context, device, host path or configuration was
changed. `SEC-003` remains pending until the official recurring RPO-24-hour
backup is implemented and restored in isolation.

On 2026-08-22 the recurring Scrutiny backup prerequisite was completed. A
daily `monitoring/scrutiny-logical-backup` CronJob uses the official InfluxDB
2.2.0 image with its compatible 2.3.0 CLI for online `influx backup`, and a
pinned Python image uses SQLite's online backup API against a read-only source
mount. The workload publishes mode-0700 copies atomically to the separate NAS
logical tree, with a lock, file/size and SHA-256 manifests, a 20-minute
deadline, `Forbid` concurrency and the existing 7/8/12/5 GFS policy. The
Operator token is available only to the backup container through the existing
Secret reference. A manual run produced one 17-file logical copy; checksums,
SQLite integrity, full isolated InfluxDB restore, offline TSM/series/WAL checks
and isolated Scrutiny 0.8.2/InfluxDB 2.2.0 startup passed. The cold bootstrap
copy and its checksums were preserved. Production Scrutiny stayed 1/1,
collectors 2/2 with recent ingestion, three nodes Ready and no unhealthy Pod.

On 2026-08-22 the separate NAS Scrutiny collector was reconciled from the
mutable `v0.8.2-collector` tag to the exact digest already running. Its
effective bytes, privilege, mounts, environment contract, six-hour schedule,
startup collection and bridge network were unchanged. The recreated collector
completed five SMART reads and five successful publications with no access,
permission or publication error; the central API confirmed the same
five-device origin and no overlap with the six active Kubernetes devices.
Kubernetes and the Scrutiny server were not modified. Native collector
migration, privilege reduction and the unrelated failed mdraid-monitoring
units remain separate work.

The follow-up NAS diagnosis confirmed one active, non-degraded mdraid array
with no resynchronization in progress. Monitoring had exited because neither a
notification address nor a notification program was configured, and the
historical local mail transport was absent. Systemd drop-ins now preserve the
vendor units while adding `--syslog`: the permanent monitor is active and the
oneshot completes successfully when the inherited `AUTOSCAN` setting is
enabled. An initial oneshot override bypassed that condition and was corrected
before commit to restore the vendor environment file and conditional command.
No array, disk, filesystem, package or mail configuration changed. Local
journal/syslog monitoring is restored; external notification remains pending
integration with Alertmanager.

Six Warning events from the removed preliminary Jobs/Pods remain as historical
evidence; no Warning occurred after final stabilization. All temporary
resources, locks and partial copies were removed. `SEC-003` remains pending;
no production privilege, image, configuration, device or hostPath changed.

On 2026-08-19 IMG-003 pinned Filebrowser from the declared `s6` tag to the
exact digest already running:
`docker.io/filebrowser/filebrowser@sha256:ee4ac79e52966a5f6247f99c7d667c1debfb277a3a61ab829f505aa8f4c74b21`.
The single-replica Recreate rollout completed with zero restarts; the Pod,
Service, EndpointSlice, HTTPRoute, Authelia, storage mounts and application
response remained healthy. No probes, resources, security context,
ServiceAccount, ports, mounts, storage, route, network or other workload
changed. SEC-003 remains pending and was not executed.

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
missing runtime evidence. It found Portainer with an unversioned
`cluster-admin` binding;
14 direct workloads use `default` ServiceAccounts with projected tokens and no
demonstrated API need; Alloy, Grafana, Loki, and kube-state-metrics have
reducible Secret-read scope. Prometheus has 24/24 active targets through ten
ServiceMonitors, with no PodMonitor, Probe, or additional scrape configuration.
See the [IAM and observability audit](../audits/KUBERNETES_IAM_OBSERVABILITY_AUDIT_2026-08-17.md).

A focused read-only Portainer diagnosis found no retained evidence that its
write, Secret, exec, RBAC, impersonation, token, node, storage, CRD, or webhook
authority has been used. Audit logs and attributable managed fields are not
available, so historical use cannot be excluded. Portainer is exposed through
its native authentication without Authelia ForwardAuth. The diagnosis proposed
a Secret-free viewer as the provisional minimum profile. On 2026-08-18 the
Platform owner selected Profile A. IAM-001 then
replaced the runtime binding with the versioned `portainer-viewer` role and
binding. The role grants explicit ordinary-resource, metrics, and Gateway API
reads plus `get` on `pods/log`; it grants no Secret, token, interactive Pod,
RBAC, CRD, webhook, certificate, or write access. The complete positive and
negative authorization matrix passed for the real identity, and Portainer,
its endpoint and route, Authelia, Traefik, and cluster health remained stable
for three post-change cycles. Authenticated visual UI validation remains
pending because no Portainer login was authorized. See the
[Portainer IAM diagnosis](../audits/PORTAINER_IAM_001_DIAGNOSIS_2026-08-17.md).

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
- Portainer IAM-001 remediation: dedicated Secret-free viewer RBAC replaced
  the unversioned `cluster-admin` binding with staged validation and rollback.
- Scrutiny collector SUP-001: pinned the existing `v0.8.2-collector` bytes by
  digest with 2/2 collectors, device counts, ingestion and drift validated.
- Scrutiny collector RES-002: added evidence-based CPU/memory requests and
  limits only; probes were found not applicable for the v0.8.2 cron model.

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
- Portainer now has only the versioned viewer RBAC, but its public route still
  relies on native authentication rather than Authelia and the authenticated
  UI was not visually validated during IAM-001.
- Alloy, Grafana, Loki, and kube-state-metrics can read Secret metadata more
  broadly than their current consumers require.
- Scrutiny collectors and server, and Jellyfin, have broad device/host access.
- Home, Authelia, and Filebrowser use mutable tags.
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

On 2026-08-19 IMG-001 pinned Home from `nginx:stable-alpine` to the exact
already-running digest
`docker.io/library/nginx@sha256:97d490c12ba55b4946b01546d1c3ed324e8d41ab1c9fcb2a616aa470620e5b46`.
The two-replica RollingUpdate completed with both Pods Ready and zero
restarts; Service, EndpointSlice, protected HTTPRoute/public response,
ConfigMap metadata and mounted files remained healthy. The controller-only
diff is empty; pre-existing full-manifest ConfigMap content drift was
preserved and not changed. No other workload or Home field changed. SEC-003
remains pending and was not executed.

On 2026-08-22 SEC-003 migrated Scrutiny 0.8.2 to Hub/Spoke with official
InfluxDB 2.2.0. Web/API now mounts only configuration and has no privilege,
capabilities, devices, udev, hostPort, Influx storage or ServiceAccount token.
An isolated API-write matrix proved minimal config ownership `0:0 0755` is
required with all capabilities dropped; retained UID 0 is the residual risk.
Three Kubernetes collectors plus NAS cover 11 active unique devices
(`2+2+2+5`); one inactive July record remains intact. A fresh logical backup
and complete isolated restore with API write and web restart passed.

## Colegio María Rosario staging — Checkpoint 1

The foundation checkpoint is deployed in namespace
`colegio-maria-rosario-staging`. It contains only the institutional web,
Service, EndpointSlice, ForwardAuth Middleware and the `colegio.*` web route.
The web image is pinned to the verified public digest
`sha256:bda565f8e529e7f897dd504e11baba21293bcc086a34ae096c36f9aa3bf20147`.

The platform Certificate includes the three educational SANs and CoreDNS
contains the three internal VIP records. Authelia has one-factor rules for the
three staging hosts; its shared `chomsmaster.com` cookie remains the explicitly
authorized temporary exception. Moodle and Gibbon are separate checkpoints and
are not part of this foundation commit.

Validation passed: Certificate Ready, CoreDNS and Authelia Ready, web
Deployment Ready, EndpointSlice present, six pages served internally,
`private-assets-review` returned 404, HTTPRoute Accepted/ResolvedRefs and
anonymous external access redirected through ForwardAuth. No Secrets or
private key material are versioned.

## Colegio María Rosario staging — Checkpoint 2

Moodle 5.2.2 and MariaDB 11.4 are deployed with independent ClusterIP
Services, PVCs and runtime Secrets. The Moodle activity validation now uses the
official assign defaults, including `visible=1`, the four required grading
fields and nullable multimarking fields. A fictional course and assign task
persist across the active PVCs; the real CronJob completed successful cycles.

The Moodle HTTPRoute for `colegio-aula.chomsmaster.com` is Accepted and
ResolvedRefs on both `web` and `websecure`, with the existing Authelia
ForwardAuth. A logical backup and isolated restore were functionally valid:
schema, fictional course, task and `moodledata/filedir` were present. The
restore marker was an artificial operational marker (`filedir`), not user
data; tar ownership warnings from local-path were handled with
`--no-same-owner` in the temporary restore only. No backup contents, Secrets or
private data are versioned.

## Colegio María Rosario staging — Checkpoint 3 declarativo

Gibbon 30.0.01 is deployed independently with its pinned bootstrap image,
dedicated MariaDB, runtime Secret, database PVC and writable application PVC.
The ClusterIP Service and HTTPRoute for `colegio-gestion.chomsmaster.com` are
attached to both Gateway listeners and the existing Authelia ForwardAuth.

The official web installer is accessible behind Authelia and the deployment is
intentionally stopped at that manual-install boundary. No installer form was
automated, no administration account was created, and no real Colegio data was
imported. The runtime PVC remains mutable as required by the official bundle;
the declarative rollback boundary covers only Gibbon resources and leaves
Checkpoints 1 and 2 intact. Runtime Secret values are not versioned.
