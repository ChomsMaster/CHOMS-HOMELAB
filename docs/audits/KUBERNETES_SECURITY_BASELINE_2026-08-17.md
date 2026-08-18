# Kubernetes Security Baseline — 2026-08-17

## Executive summary

This is a non-mutating security, resilience, and maintainability baseline for
CHOMS Platforms. It correlates the desired state at commit
`2f35d04c5fb1db0a2f0f25406f9068f817818217`, the last versioned runtime
observation from 2026-08-17, the 2026-08-16 workload audit, and safe anonymous
HTTPS observations made on 2026-08-17. It contains no Secret values, private
topology, user data, backup contents, or administrative addresses.

No Kubernetes resource, Helm release, node, network rule, certificate, DNS
record, or workload was changed. MetalLB speaker remains **Blocked**. Its
rollout was not retried.

The platform has strong foundations: Git ownership for all known workloads,
locked Helm releases, immutable images for most direct workloads, safe rollout
strategies for persistent single-replica databases, useful probes, centralized
TLS, established database/Nextcloud backup automation, and an append-only
operational memory. The largest actionable gaps are public access to an
unprotected Prometheus UI, broad device privileges in Scrutiny and Jellyfin,
the absence of namespace network isolation, incomplete workload security
contexts and ServiceAccount-token controls, and a same-NAS backup failure
domain.

No Critical finding was established. Findings are deliberately not inflated:
uncorroborated runtime claims are labelled **Needs evidence**, and functional
privileges are not treated as removable until their device requirements are
tested.

## Methodology and evidence boundaries

The audit used only read-only operations:

- complete review of repository instructions, active operational memory,
  ADRs, architecture, operations, backup documentation, existing audits,
  direct manifests, vendored MetalLB resources, Helm values, and automation;
- structural parsing of all versioned Kubernetes YAML without rendering or
  applying it;
- review of image references, probes, resources, security context, RBAC,
  storage, routes, authentication filters, Secret references, and backup code;
- tracked-file scanning for likely credentials, private keys, tokens, dumps,
  and accidentally versioned sensitive files;
- anonymous, non-invasive HTTP(S) requests limited to declared public routes;
- comparison with the last versioned runtime evidence in
  `docs/context/CURRENT_STATE.md` and
  `docs/operations/KUBERNETES_WORKLOAD_AUDIT.md`.

The audit environment did not provide `kubectl`, `helm`, `k3s`, or `yq`, and
the control-plane hostname was not resolvable from it. No tool was installed,
no internal address was used as a fallback, and no `sudo` command was run.
Consequently, live API objects, current `imageID` values, events, restart
counts, EndpointSlices, effective Helm rendering, RBAC bindings created outside
Git, Prometheus targets, alerts, and logs could not be independently sampled in
this session. These checks are listed as **Needs evidence**. The last durable
runtime observation reported three Ready nodes, 35 attributed workloads, all
PVCs Bound, six deployed Helm releases, and no failed or pending Pods.

Historical Docker-era documents contain internal topology and sometimes call
Compose the active deployment model. They were read as engineering history;
the active Kubernetes memory and ADRs take precedence.

## Quantified inventory

### Desired state and last observed runtime

| Domain | Git or last observed count | Evidence status |
|---|---:|---|
| Active runtime namespaces | 17 | Last observed 2026-08-16 |
| Active workloads | 35 | Last observed: 17 direct, 15 Helm, 3 K3s-managed |
| Direct Deployments | 15 | Parsed from Git |
| Direct DaemonSets | 2 | Parsed from Git |
| Direct StatefulSets | 0 | Parsed from Git |
| Direct Jobs / CronJobs | 0 / 0 | Parsed from Git; live confirmation pending |
| Versioned Services | 15 | Parsed from Git, including MetalLB webhook |
| Versioned HTTPRoutes | 14 | Parsed from Git |
| Versioned IngressRoutes | 1 | Traefik dashboard |
| Versioned PVCs | 8 | Plus three chart-configured persistent claims |
| Locked Helm releases | 6 | Git and last observed runtime |
| Versioned Certificates / ClusterIssuers | 1 / 1 | Git; last certificate was Ready |
| Vendored MetalLB CRDs | 8 | Git |
| Direct ServiceAccounts | 3 | Portainer and two MetalLB accounts |
| Direct Roles / ClusterRoles | 2 / 2 | Vendored MetalLB |
| Direct RoleBindings / ClusterRoleBindings | 2 / 2 | Vendored MetalLB |
| NetworkPolicies | 0 | Git; live confirmation pending |
| PodDisruptionBudgets | 0 | Git; live confirmation pending |
| HPAs | 0 | Git; live confirmation pending |
| ResourceQuotas / LimitRanges | 0 / 0 | Git; live confirmation pending |

The 97 parsed versioned Kubernetes objects comprise 15 Deployments, two
DaemonSets, 15 Services, 14 HTTPRoutes, eight PVCs, eight CRDs, seven
Namespaces, seven ConfigMaps, the RBAC objects above, three Middleware
resources, one IngressRoute, one Certificate, one ClusterIssuer, one
IPAddressPool, one L2Advertisement, one template Secret, and one validating
webhook configuration. Runtime-generated ConfigMaps, Secret objects,
EndpointSlices, chart resources, and system resources are intentionally not
inferred from that count.

### Direct workload control coverage

| Control | Coverage | Interpretation |
|---|---:|---|
| Immutable digest | 13/17 workloads | Four direct tags remain |
| Full startup/readiness/liveness | 9/17 | Main containers; init containers assessed separately |
| Readiness+liveness, no startup | 7/17 | Often acceptable for fast-starting services, but must be justified |
| No probes | 1/17 | Scrutiny collector |
| Complete requests and limits | 9/17 | Main containers |
| Partial resources | 4/17 | Usually missing CPU limit |
| No resources | 4/17 | MariaDB, both MetalLB workloads, collector |
| Strong container baseline | 1/17 | CHOMS Controller |
| Dedicated ServiceAccount | 3/17 | Portainer, MetalLB controller and speaker |
| Explicit token automount disable | 0/17 | All direct Pod specs leave the default |
| Privileged | 3/17 | Jellyfin, Scrutiny server, Scrutiny collector |
| HostPath/device access | 4/17 | Jellyfin, both Scrutiny roles, qBittorrent |
| Host network | 1/17 | MetalLB speaker, functionally expected for L2 |
| Host ports | 1/17 | qBittorrent TCP/UDP peer port |

## Workload inventory and assessment

The runtime image column below uses the last durable observation. `Same bytes`
means the observed runtime tag resolved to the digest already in Git; it does
not mean declarative drift was absent.

| Workload | Owner/source | Desired image class | Last runtime relation | Resilience and security summary | Exposure / consumers | Recovery |
|---|---|---|---|---|---|---|
| CHOMS Controller | Direct `apps/choms-controller.yaml` | Digest | Matched | Recreate; full probes/resources; non-root, read-only root, no escalation, drop ALL; default SA token remains | Public API route; PostgreSQL consumer | Stateless; database recovery applies |
| Home | Direct `home/home.yaml` | Mutable tag | Effective digest known | 2 replicas, RollingUpdate, full probes/resources; root/default context; no PDB or spread constraints | Root public; secondary hostname via Authelia | ConfigMap content in Git |
| Nextcloud | Direct `apps/nextcloud.yaml` | Main+init digests | Matched | Recreate; full main probes/resources; root main and root storage init; RWX NFS | Native login and public-link policy; MariaDB/Redis/NAS | Consistent snapshot + DB dump; restore tested |
| Portainer | Direct `apps/portainer.yaml` | Digest | Registry-prefix drift only | Recreate; full probes/resources; dedicated SA but effective RBAC needs evidence; root/default context | Public route with native authentication | PVC on NAS; no workload-specific restore test documented |
| Uptime Kuma | Direct `apps/uptime-kuma.yaml` | Digest | Registry-prefix drift only | Recreate; full probes/resources; root/default context | Public route with native UI | PVC on NAS; no specific restore test |
| MariaDB | Direct `databases/mariadb.yaml` | Digest | Matched | Recreate; full probes; no resources; root/default context; RWX used by one replica | ClusterIP; Nextcloud | Logical backup succeeds per last evidence; restore covered through Nextcloud test |
| PostgreSQL | Direct `databases/postgres.yaml` | Digest | Same bytes; tag was reconciled later | Recreate; full probes/resources; `fsGroup`; root not prohibited | ClusterIP; CHOMS Controller | Logical dump validation; no documented full application restore drill |
| Redis | Direct `databases/redis.yaml` | Digest | Same bytes; later reconciled | Recreate; full authenticated probes/resources; root/default context; RWX one replica | ClusterIP; Nextcloud and Authelia use separate credentials/instances logically | RDB backup and validation; restore drill not documented |
| Authelia | Direct `authelia/authelia.yaml` | Version tag | Effective digest known | Recreate; full probes/resources; root/default context | Public identity endpoint; ForwardAuth for selected routes | PVC plus Redis; specific restore test absent |
| Filebrowser | Direct `filebrowser/filebrowser.yaml` | Mutable tag | Effective digest known | Recreate; R/L only; CPU limit absent; root/default context; direct NFS mounts | Public route with native login | NAS data; no specific restore test |
| Jellyfin | Direct `jellyfin/jellyfin.yaml` | Digest | Matched | Recreate; R/L only; CPU limit absent; privileged with host config/cache/media/device paths; node-pinned | Public native login; media devices | Host/NAS paths; recovery and hardware-transcode rollback need design |
| Threadfin | Direct `threadfin/threadfin.yaml` | Digest | Matched | Recreate; R/L only; complete resources; root/default context | Authelia protected; Jellyfin consumer | PVC on NAS; no specific restore test |
| qBittorrent | Direct `qbittorrent/qbittorrent.yaml` | Digest | Matched | Recreate; R/L only; CPU limit absent; node-pinned host config and host peer ports | Public native login plus peer ports | Host config/NAS downloads; no specific restore test |
| Scrutiny server | Direct `scrutiny/server.yaml` | Digest | Matched | Recreate; R/L only; CPU limit absent; privileged with broad host paths and devices; node-pinned | Public UI; collector ingestion | Host DB/config; backup and restore evidence absent |
| Scrutiny collector | Direct `scrutiny/collectors.yaml` | Version tag | Effective digest known | DaemonSet; no probes/resources; privileged host device access; default SA/token | Scrutiny server | Telemetry reconstructible; device discovery must be preserved |
| MetalLB controller | Vendored native manifest | Digest | Reconciled and validated | R/L; no resources; non-root Pod, read-only root, no escalation/drop all; dedicated RBAC | Edge controller/webhook | Git recreation; rollback validated |
| MetalLB speaker | Vendored native manifest | Digest | Runtime intentionally rolled back to tag, same bytes | HostNetwork, `NET_RAW`, read-only root; no resources; memberlist and status conflict unresolved | L2 edge; metrics gap | **Blocked**; do not retry rollout |

Helm-rendered workloads remain owned by their six locked charts. The observed
15 workloads include cert-manager components, Traefik, the NFS provisioner,
Prometheus stack workloads, Loki, Alloy, and their sidecars/init containers.
They must be changed only through locked chart versions and versioned values.
The values provide explicit resources for the principal Prometheus,
Alertmanager, Grafana, operator, Loki, gateway, and Alloy containers, but chart
sidecars/init containers have uneven controls. Effective rendered security,
probes, RBAC, token mounts, PDBs, and images require a fresh Helm/runtime
capture.

K3s owns CoreDNS, metrics-server, and local-path-provisioner. They are not
direct-manifest remediation targets.

## Image and supply-chain baseline

### Direct images

- **Digest-pinned:** 13 of 17 workloads, plus the Nextcloud BusyBox init
  container. Digests preserve reproducibility but do not establish provenance,
  signatures, SBOM availability, or vulnerability status.
- **Tags pending pinning:** Home (`stable-alpine`), Authelia (version tag),
  Filebrowser (`s6`), and Scrutiny collector (version tag). Their effective
  digests were known in the prior audit; a fresh runtime `imageID` must be
  captured before any pin-only change.
- **`latest`:** none in current workload templates. Historical Pod display
  names are not desired-state evidence.
- **Git already equals effective bytes:** the earlier PostgreSQL and Redis tag
  drift was reconciled successfully. MetalLB controller was reconciled.
  MetalLB speaker is the explicit exception: Git holds the digest, runtime was
  rolled back to the matching version tag after the failed rollout.
- **Low registry-prefix drift:** Portainer and Uptime Kuma previously differed
  only by an explicit registry prefix. Reconciliation would still restart a
  Pod and is not justified as an isolated priority.
- **Unattributed digest:** none in the last complete audit; current attribution
  needs a fresh runtime capture.

### Helm, vendored, init, and sidecar images

Most chart-managed images use chart-versioned tags. The Alloy config reloader
was the observed digest exception. These images are not to be edited on
rendered workloads; pinning feasibility must be evaluated release by release
against chart-supported values. The vendored MetalLB controller and speaker
are digest-pinned in Git. The prior audit recorded exact image IDs for all
chart main containers, sidecars, and init containers, but they are historical
evidence rather than a current vulnerability assessment.

No registry signature policy, admission policy, SBOM verification, provenance
verification, or automated image vulnerability gate is versioned. This is a
Medium supply-chain maturity gap, not proof that any current image is
vulnerable.

### Rollout sensitivity

Backups or explicit reconstruction paths are required before changing
Nextcloud, MariaDB, PostgreSQL, Redis, Portainer, Uptime Kuma, Authelia,
Threadfin, Grafana, Prometheus, Loki, NFS provisioner, Scrutiny state, or any
host-path configuration. Edge changes require continuous route monitoring.
Jellyfin and Scrutiny changes require device/function testing. MetalLB speaker
requires the separately blocked network/status investigation before any
rollout.

## Workload security and resilience findings

### Existing controls

- All three persistent single-replica databases now use `Recreate`.
- Nine direct main containers have full startup/readiness/liveness coverage;
  seven have readiness and liveness; only the collector has none.
- Nine direct main containers have both requests and limits.
- CHOMS Controller provides the best direct security-context baseline.
- MetalLB controller and speaker use read-only roots, block privilege
  escalation, and drop capabilities; speaker adds only `NET_RAW` in the
  vendored definition.
- No direct workload declares hostPID or hostIPC.
- Public application Services are normally ClusterIP and route through
  Traefik; the principal intended exception is the Traefik LoadBalancer.
- Persistent database rollouts have explicit health checks and documented
  consumer validation patterns.

### Gaps and distinctions

- **Correctable insecurity:** most direct workloads omit explicit
  `runAsNonRoot`, `allowPrivilegeEscalation`, capability drops, seccomp, and
  read-only-root settings. These must be tested per image and volume ownership;
  they are not safe as a blanket patch.
- **Functionally necessary privilege pending minimization:** Jellyfin requires
  media device access; Scrutiny requires SMART/device discovery; MetalLB
  speaker requires host networking and L2 capability. The goal is a narrower
  device/capability mapping that demonstrably retains functionality.
- **Inherited/default behavior:** 14 direct workloads use the `default`
  ServiceAccount and all 17 leave token automount at the default. Most do not
  call the API and should be candidates for `automountServiceAccountToken:
  false`, verified one workload at a time.
- **Availability:** most direct workloads are one replica, have no PDB, and
  several are intentionally node-pinned. PDBs do not create capacity and are
  not useful for every singleton; first document disruption behavior and
  recovery expectations.
- **Distribution:** Home has two replicas but no explicit anti-affinity or
  topology spread. Runtime placement needs evidence before classifying the
  practical failure domain.
- **Storage:** RWX claims used by singleton databases are safe only because
  `Recreate` prevents concurrent Pods. Policy and admission checks should guard
  against regression.
- **Rollback:** revision history exists for Deployments, Helm uses atomic
  upgrades, and Git records desired state. Data-schema rollback remains a
  separate recovery concern.

## Network, edge, and exposure

Git declares 14 Gateway API HTTPRoutes and one Traefik IngressRoute. Both HTTP
and HTTPS listeners accept routes from all namespaces. Cross-namespace route
attachment is intentional but broad; namespace admission and route ownership
should be reviewed.

Authelia ForwardAuth is explicitly applied to Home, Threadfin, and the Traefik
dashboard. Other routes rely on native authentication or are intentionally
public. The manifests do not encode a per-route rationale, making accidental
public exposure harder to detect.

Anonymous HTTPS observations succeeded with certificate verification for all
declared hostnames. Home and Threadfin redirected to Authelia as expected;
Nextcloud, Grafana, Jellyfin, Kuma, and Scrutiny redirected to their native
entry points; the public site loaded; controller and the dashboard root
returned 404 (the dashboard is path-scoped). Portainer, Filebrowser, and
qBittorrent returned application responses consistent with native entry
pages. No authentication bypass was attempted.

Prometheus redirected anonymously to its query interface and has no
ForwardAuth filter in Git. This makes operational metrics and labels publicly
reachable unless an unobserved application-side control exists. It is a High
finding because the manifest and anonymous behavior agree. Protecting it is
the first small, reversible hardening candidate.

Plain HTTP requests to a representative sample returned `400` rather than an
HTTPS redirect. Sampled HTTPS responses did not consistently expose HSTS;
application security headers varied. This is a Medium edge-policy gap pending
confirmation at Traefik and any upstream proxy. It is not a TLS failure: TLS
verification succeeded.

No NetworkPolicy is versioned. Database, storage, monitoring, and application
namespaces therefore have no Git-defined east-west allowlist. There are no
versioned NodePort application Services. qBittorrent intentionally declares
TCP/UDP host ports for peer traffic, and MetalLB speaker uses hostNetwork.
Internal databases and NFS are not routed through public HTTPRoutes.

Split DNS is versioned in a CoreDNS custom ConfigMap, while historical network
documents expose obsolete literal topology. DNS resolution and parity between
public and internal answers require a privileged/on-LAN verification and are
not reproduced here.

## RBAC and Secret handling

### RBAC

The only direct versioned RBAC is the vendored MetalLB policy. It includes
wildcard verbs for `ServiceL2Status` and `ServiceBGPStatus`, scoped to those
status resources. This is broad but upstream-functional, and the observed
immutable-node conflict means it must be understood before narrowing or
changing ownership. Controller permissions include Secret lifecycle and
webhook/CRD management expected by the vendored installation.

Portainer has a dedicated ServiceAccount in Git but no versioned RoleBinding or
ClusterRoleBinding. Its effective runtime permission and intended management
scope are **Needs evidence**. The other direct applications primarily use the
default ServiceAccount. Effective chart and K3s RBAC, wildcard permissions,
and administrative bindings require a live API inventory.

### Secrets

- Secret values are absent from tracked Kubernetes desired state and are
  created from a local ignored environment file.
- The ignored local file exists but was not opened or inspected.
- Tracked-file scans found no private-key block, JWT, common GitHub token, or
  obvious literal credential. Matches in backup scripts were variable
  references, not values.
- The vendored MetalLB template includes a Secret object name without Secret
  data.
- Secret references and object names are versioned where needed; runtime
  Secret values and encoded fields were never requested.
- Bootstrap depends on a manually protected local environment file and remote
  SSH execution. Rotation cadence, escrow/recovery, ownership, and expiry are
  not documented per Secret.
- MariaDB credentials are duplicated into the database and consumer
  namespaces. The Kubernetes backup script reads the consumer-namespace copy
  while operating on the database Pod; correctness depends on both copies
  remaining equal. Last backups succeeded, but this is avoidable coupling.

## Persistence, backup, and recovery

| Data domain | Storage | Backup/control | Restore evidence | Residual risk |
|---|---|---|---|---|
| MariaDB / Nextcloud DB | NFS PVC, singleton Recreate | Logical dump in platform backup and consistent Nextcloud workflow | Isolated Nextcloud DB restore passed 2026-08-14 | Credential-copy coupling; current success needs live evidence |
| PostgreSQL | NFS PVC, RWO, singleton Recreate | Custom-format logical dump and structure validation | No documented full consumer restore drill | RTO/RPO absent |
| Redis | NFS PVC, singleton Recreate | SAVE, RDB validation and copy | No documented isolated restore drill | RTO/RPO absent |
| Nextcloud files/config/apps/themes | NFS PVC | Maintenance-mode DB dump plus reflink snapshot/checksums/GFS | Controlled restore validation documented | Same NAS failure domain |
| Grafana / Prometheus / Loki | Chart PVCs on NFS | NAS/storage dependence; no workload-specific restore procedure found | None documented | Dashboards/history loss and single NAS dependency |
| Portainer, Kuma, Authelia, Threadfin | NFS PVCs | Underlying NAS may preserve files; no application-consistent procedure found | None documented | Recovery semantics and RTO/RPO absent |
| Jellyfin, Scrutiny, qBittorrent | HostPath and/or NAS paths | No complete workload-specific backup mapping found | None documented | Node affinity and local-path SPOF |
| Kubernetes desired state | Git plus runtime inventory excluding Secrets | Versioned manifests and scheduled non-Secret inventory | Declarative rebuild documented | Secret recovery is external/manual |

All observed PVCs were Bound in the last runtime evidence. GFS automation uses
checksums and atomic publication. Nextcloud restore testing is the strongest
recovery control. However, NAS reflinks and promoted hard links remain on the
same storage failure domain, so they do not protect against total NAS loss.
There is no versioned RPO/RTO matrix. The Kubernetes inventory backup excludes
Secrets correctly, but the protected procedure for restoring Secret material
is not documented in this repository.

## Observability

The platform has Prometheus, Alertmanager, Grafana, Loki, Alloy,
kube-state-metrics, node-exporter, Uptime Kuma, and Scrutiny. Prometheus values
enable broad ServiceMonitor, PodMonitor, Probe, and rule selection; retention
is 15 days/17 GB. Loki is monolithic with one replica, filesystem storage,
seven-day retention, and authentication disabled behind its internal gateway.
Alloy runs as a DaemonSet, discovers same-node Pod logs, and forwards cluster
events and CRI logs to Loki. Grafana uses existing-Secret admin credentials and
disables analytics reporting.

Controls and gaps:

- node and Kubernetes object telemetry is present through the monitoring chart;
- log and Kubernetes-event collection is versioned across nodes;
- Loki and Prometheus are single replicas on NFS, so observability shares the
  storage failure domain it is expected to diagnose;
- exact active targets, failing scrapes, alert rules, firing alerts, dashboard
  coverage, and Alertmanager receiver delivery are **Needs evidence** because
  live tools were unavailable;
- no versioned Alertmanager receiver configuration is visible in the supplied
  values, so notification delivery must be verified rather than assumed;
- database/application-specific exporters and ServiceMonitors are not evident
  for every direct workload;
- backup timer success is documented but no clearly versioned Prometheus alert
  for backup age/failure was found;
- MetalLB speaker `/metrics` is an explicit **Blocked** observability gap: native
  kubelet probes pass, but prior cross-node/API-proxy/port-forward attempts
  could not reach metrics and Prometheus showed no active matching target. Do
  not change or restart speaker to investigate it.

## Findings by severity

### Critical

None established.

### High

1. **Public Prometheus query interface without declared edge authentication.**
   Anonymous behavior and Git agree. Metrics can reveal operational labels and
   system behavior even when no Secret values are exposed.
2. **Privileged device workloads.** Jellyfin and both Scrutiny roles have broad
   host/device reach. This is a host-compromise path, but privilege is currently
   functionally motivated and must be narrowed through hardware tests.
3. **No independent/off-site backup copy.** Total NAS loss can affect live data,
   PVCs, snapshots, and promoted backup tiers together.

### Medium

1. No versioned NetworkPolicies or staged namespace isolation.
2. Four direct workload tags remain unpinned; current image IDs need fresh
   confirmation before pinning.
3. Security contexts and ServiceAccount-token controls are missing on most
   direct workloads.
4. Scrutiny collector has no probes or resources; MariaDB and MetalLB lack
   resources; four application workloads have partial limits.
5. Plain HTTP does not demonstrably redirect to HTTPS and HSTS/header policy is
   inconsistent in the safe sample.
6. Application-consistent recovery and RPO/RTO are incomplete outside the
   database/Nextcloud path.
7. MariaDB backup depends on duplicated cross-namespace credential material.
8. Observability target/alert delivery coverage is not continuously evidenced;
   Prometheus/Loki are single-replica and NAS-dependent.
9. Route authentication intent is implicit rather than recorded per public
   service.
10. Supply-chain verification stops at digests/locked charts; signatures,
    provenance, SBOM, scanning, and admission policy are absent.

### Low

1. Registry-prefix-only drift for Portainer and Kuma can wait for a useful
   workload change.
2. Home has two replicas but no explicit spread/PDB evidence.
3. Historical Docker documentation contradicts the active Kubernetes model and
   contains topology that should eventually be classified or redacted through
   a dedicated documentation consolidation task.
4. The Traefik dashboard root returns 404 by design because only `/api` and
   `/dashboard` are routed; this is not an availability finding.

### Accepted or documented exceptions

- MetalLB speaker hostNetwork and `NET_RAW` are expected for L2 operation.
- Node-exporter host namespaces and mounts are chart-managed monitoring needs.
- Root ownership-init behavior for Nextcloud/Grafana may be required for NFS
  permissions and must not be removed without a tested replacement.
- qBittorrent peer host ports are functionally intentional; public UI exposure
  is a separate control.
- Single replicas are accepted for current scale where recovery and downtime
  are understood; a PDB alone would not create availability.

### Blocked

- **MetalLB speaker:** remain Blocked until an authorized platform operator can
  perform the required
  privileged node readings, TCP/UDP 7946 connectivity is understood and
  corrected under separate network authority, `ServiceL2Status` ownership is
  explained, all speakers converge, and metrics scraping is proven. No rollout
  was attempted in this audit.

### Needs evidence

- current nodes/Pods/workload readiness, restarts, events, EndpointSlices, PVC
  state, StorageClasses, live CRDs, Ingress, PDB/HPA/quota/policy inventory;
- current runtime declarations and effective `imageID` values;
- effective Helm resources, chart RBAC, ServiceAccounts, rendered security
  contexts, and release revisions;
- active Prometheus targets, ServiceMonitors/PodMonitors, rules, alerts,
  dashboards, Alertmanager receivers, Loki ingestion, and retention behavior;
- current backup timer results and non-sensitive age/status evidence;
- runtime Portainer RBAC and any unversioned administrative bindings;
- split-DNS results and node-level storage/firewall evidence that requires
  on-LAN or privileged access.

## Recommended verification criteria

Every later hardening task must remain one workload or one logical block and
must include:

1. clean, synchronized Git and fresh non-sensitive runtime evidence;
2. explicit owner, consumers, exposure, backup/reconstruction path, and rollback;
3. local validation, server dry-run and exact `kubectl diff` for direct
   manifests, or locked Helm plan for chart resources;
4. no unexpected diff and no Secret value output;
5. rollout/probe/resource/storage/endpoints/route/auth/consumer validation;
6. multiple steady-state observation cycles and recent event review;
7. final drift zero, cluster health, clean tree, commit, push, and operational
   memory update.

For security-context or device changes, additionally prove entrypoint UID/GID,
filesystem/PVC ownership, required syscalls/capabilities/device nodes, and the
real functional path (SMART discovery or hardware transcode). For network
policy, begin with flow inventory and explicit allowlists before default deny.

## SEC-002 focused follow-up — 2026-08-18

Temporary canaries using the pinned Scrutiny v0.8.2 collector image tested the
two collector nodes independently without uploading data. The privileged
reference discovered and read two devices per node. The proposed
non-privileged root profile with only `SYS_RAWIO`, all other capabilities
dropped, no privilege escalation and `RuntimeDefault` seccomp discovered the
same devices but failed every device open. Removing seccomp did not help, and
granting every capability while remaining non-privileged produced the same
result. The limiting layer is therefore the K3s/containerd device cgroup, not
Unix UID, `SYS_RAWIO`, or seccomp.

Individual block-device `hostPath` volumes cannot be supplied through
`volumeDevices`; Kubernetes validation accepts only PVC or Ephemeral sources
for block mode. A separate read-only-rootfs experiment failed before cron
started because the v0.8.2 entrypoint writes its environment and cron
configuration, and cron requires writable runtime state. Under
`privileged: true`, seccomp and AppArmor are unconfined, all capabilities are
granted and `allowPrivilegeEscalation` is effectively true, so declaring those
fields would not provide a real compensating control.

No DaemonSet change was made. SEC-002 is blocked until the platform adopts a
supported per-device mapping mechanism, such as a reviewed device plugin, CDI,
DRA, or an equivalent K3s/containerd integration that creates explicit device
cgroup rules and remains stable on both nodes. All temporary resources were
removed and production health and drift remained unchanged.

## Top ten ordered follow-up blocks

1. Protect only the Prometheus HTTPRoute with the existing Authelia middleware;
   validate anonymous redirect, authenticated access, alerts, and scraping.
2. Capture the complete read-only runtime/RBAC/observability inventory from an
   authorized workstation and reconcile this report's Needs evidence items.
3. Pin only the Scrutiny collector's currently effective digest, without
   changing privilege, then validate ingestion on both collector nodes.
4. Add conservative collector resources and only probes supported by its
   execution model; keep device access unchanged in that task.
5. Design and test Scrutiny privilege/device minimization with an isolated
   rollback and verified SMART discovery.
6. Create an encrypted backup copy outside the live NAS failure domain and run
   a documented restore validation.
7. Inventory east-west flows and stage NetworkPolicies one namespace at a time,
   starting with databases without enforcing an untested default deny.
8. Disable ServiceAccount token automount one direct workload at a time where
   API access is proven unnecessary, beginning with a stateless low-risk app.
9. Pin Home, Authelia, and Filebrowser one at a time from freshly observed
   effective image IDs, with route/storage/auth validation.
10. Define RPO/RTO and application-consistent restore tests for PostgreSQL,
    Redis, Grafana/Prometheus/Loki, and stateful application PVCs.

MetalLB speaker is deliberately outside this execution order while Blocked.

## Conclusion

CHOMS Platforms is reproducible and operationally disciplined, but not yet
least-privilege or failure-domain complete. The safest next improvement is a
small edge-policy change protecting Prometheus, followed by a fresh privileged
read-only evidence capture by an authorized platform operator. This audit
records proposals only; it did not remediate or operationally change the
platform.
