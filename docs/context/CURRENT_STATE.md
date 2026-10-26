## CHOMS Skills — promoción local, 26-10-2026

Perfil canónico 1.0.0 en [tools/choms-skills](../../tools/choms-skills/README.md),
adaptado de ECC v2.2.3 con commit, licencia y SHA-256 fijados. Seis skills
activadas mediante enlaces individuales en las raíces nativas de Codex y Hermes;
la variante MCP se llama `choms-mcp-server-patterns`. Verification queda en
optional/, sin enlace ni descubrimiento. Codex skills/list: 6 habilitadas, cero
errores; Hermes: listado, parseo y expansión slash 6/6, sin inferencias.
No se amplían toolsets: Hermes usa carga explícita, sin habilitar skill_manage.
Configuraciones y OAuth intactos; sin hooks, aprendizaje, memoria ECC ni MCP
nuevos. Cognee + Codebase Memory siguen siendo la única memoria oficial.
Evidencia acotada en [DISCOVERY_VALIDATION.json](../../tools/choms-skills/DISCOVERY_VALIDATION.json).
Este bloque no consulta ni modifica Kubernetes ni repite pruebas de Cognee.

## Cognee — backup/restore aceptado, 26-10-2026

Backup set `20261025T222914Z-2e9b33c6`, marker
`062cfac7883306df2e5d13a92b6e8bf367dfe91049d0b184e26d9f027fceba41`:
restore aislado PASS con 36 documentos, 2.226 nodos y 6.040 aristas; RTO 482,09 s.
Confirmación del operador: live Ready, temporales eliminados, snapshots y OCI
preservados. Restore PostgreSQL por archivo tmpfs verificado; omite solo
`COMMENT - EXTENSION vector` y mantiene vector 0.8.2 propiedad de postgres, tablas como
cognee y --exit-on-error. No se repitió backup/restore ni sudo durante el cierre.
RPO periódico/offsite/automatización pendientes. Evidencia y límites en
[runbook](../operations/COGNEE_BACKUP_RESTORE.md). Siguiente bloque: MCP, todavía
no desplegado y sujeto a autenticación/compatibilidad/handshake.

## Cognee — cierre funcional verificado, 25-10-2026

API y PostgreSQL/pgvector Ready en node-02, solo ClusterIP. Tras la ampliación
se aplicó request 8 GiB / limit 16 GiB, sin cambiar CPU, imagen ni modelos.
Un solo cognify terminó con 36/36 documentos: pico cgroup 12,20 GiB, cero OOM,
cero reinicios y cero intentos HTTP no autorizados registrados por la guarda.
Consulta trazable y persistencia tras un único restart API: PASS; 2.226 nodos
y 6.040 aristas conservados. Consultar por API HTTP: un segundo cliente SDK
puede competir por el bloqueo de archivos del grafo local.
MCP no admitido (auth entrante/compatibilidad pendientes); no se desplegó.
El bloque backup/restore se aceptó posteriormente; véase el cierre del 26-10-2026 arriba.
El historial inferior conserva fases anteriores; este cierre actualiza su estado.
Véase [operación](../operations/MEMORY_PLATFORM.md).

## Presentación y custodia — 24-10-2026

Documentación pública simplificada; README sin IPs internas ni endpoints administrativos. Roadmap raíz reconcilia evidencia de
código con aceptación operacional pendiente. Recipient público documentado;
configuración auxiliar de cifrado en custodia, sin generación de kit real.
La descripción/topics de About solo se proponen; no se aplican en GitHub.

# Cambio de alcance local — kit privado de recuperación

El diseño cloud previo queda retirado del código. Se prepara un kit offline
cifrado de configuración en un repositorio independiente y un runbook de
reconstrucción; ninguno se ha ejecutado. Trivy pasa a informativo, manteniendo
hallazgos en docs/SECURITY_BACKLOG.md. No cambia el estado de producción.

# Estado de referencia — actualización documental 23-10-2026

La fuente real de este bloque es el inventario entregado por el propietario; no
se consultó producción. Registra 3 nodos, 18 namespaces, 41 controladores
(33 Deployments/3 StatefulSets/5 DaemonSets), 2 CronJobs, 6 Helm releases,
9 Pods Error históricos y 6 PVs Released/Retain. Colegio usa también local-path.
Véase [baseline](../inventory/BASELINE_2026-10-23.md). Los estados históricos de
salud, números y pendientes del texto inferior conservan sus fechas, y no son
una comprobación actual. Este bloque solo prepara código/documentación: políticas,
Terraform y CronJob NO desplegados; offsite y adopción NO ejecutados.

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
- Media and utilities: Jellyfin, Filebrowser.
- Observability: Prometheus, Alertmanager, Grafana, Loki, Alloy, Scrutiny.

Runtime namespaces include `apps`, `databases`, `security`, `traefik`,
`metallb-system`, `cert-manager`, `monitoring`, `logging`, `media`,
`filebrowser`, and `nfs-provisioner`, plus Kubernetes system
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

An encrypted restic recovery copy is active on node-03 and declared under
[`stacks/backup/restic/`](../../stacks/backup/restic/). The repository resides
on the existing ext4 HDD at
`/mnt/choms-local/backups/choms-platforms-restic`; node-01 and node-02 use
source-restricted SFTP and node-03 uses the same repository locally. Restic
encrypts and deduplicates at source, while the repository password is absent
from Git and requires external custody. Six hostname/type snapshot categories
cover the validated database package, authorized small platform/Kubernetes
state, encrypted Secret exports, consistent SQLite K3s state, selected
Nextcloud configuration/application state, Jellyfin configuration. Historical full-platform figures follow: The validated aggregate is 1,242,635,604 logical
bytes and 1,108,695,459 stored bytes, below the 25 GiB guard.

Bulk Nextcloud data, multimedia, downloads, Colegio, personal or historical
backups, Prometheus TSDB, Loki, caches and unrelated `/srv/storage` content are
excluded. Backup timers are active and waiting at 05:00, 05:30 and 06:00, with
maintenance at 06:30 Europe/Madrid. Retention is declared as 7 daily, 4 weekly
and 6 monthly, but maintenance currently performs only `forget --dry-run`;
real forget, prune and automatic unlock remain disabled. Monitoring ingests
Restic metrics from all three nodes and has two loaded critical rules. The
controlled notification signal completed one FIRING/RESOLVED cycle, was
removed, and ended inactive.

Kubernetes and Nextcloud backup services most recently reported success during
the 2026-08-17 observation. The last documented Nextcloud restore validation
completed on 2026-08-14. The encrypted node-03 copy is separate from the NAS
failure domain, but remains local rather than offsite and therefore does not
protect against loss of the site or its recovery HDD. Recovery requires that
HDD, the externally held password and a compatible Restic version. See
[`stacks/backup/README.md`](../../stacks/backup/README.md).

On 2026-08-30 the fixed Kubernetes package `20260830-031918` passed a complete
isolated database recovery test. With the production image digests, temporary
credentials, three independent local-path PVCs and namespace-wide default-deny
network policy, MariaDB restored 1 database/127 tables in 24.880 seconds,
PostgreSQL restored 1 non-system schema/1 table in 2.573 seconds, and Redis
loaded 6 keys in 1.061 seconds. Each engine passed a write/read/delete probe;
eight non-sensitive configuration files were structurally extracted without
being applied. The namespace exposed no endpoint, production and monitoring
resource versions did not change, the critical-alert count had zero delta, and
guarded cleanup removed the namespace, PVCs, PVs and Secret without a Released
PV. The reusable test script records only aggregate evidence. Off-site copies,
external Secret recovery and coverage for the remaining stateful services/PVCs
remain open risks.

## Restic node-01 freshness correction — 2026-09-23

The deployed node-01 correction removes the fixed 2026-08-30 package reference,
selects and validates the newest package without falling back to an older one,
and enforces a maximum 24-hour RPO. Logical scope is measured from the authorized
sources instead of a constant. Last successful execution and protected package
freshness are recorded separately.

The operator's controlled run at 20:49:42–20:49:59 CEST succeeded in 17 seconds,
with 167,611,546 logical bytes and package age 63,113 seconds. Read-only closure
checks matched both installed script hashes to the prepared files, confirmed the
timer enabled/active/waiting and service inactive/dead with Result=success,
and matched all nine metrics in Prometheus with zero Restic firing alerts.
Last success is 1790189399; protected package timestamp is 1790126274.
Bash syntax and 56 synthetic checks passed; ShellCheck remains unavailable.
The root-only rollback is retained. Node-02/node-03 constant sizes remain pending
debt, and this encrypted copy remains local rather than offsite. The historical
scope validator still needs a separately authorized update for newer packages.
Commit/push are pending manual execution because Git metadata is read-only here.

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

On 2026-08-29 the NAS collector's stale pre-Hub/Spoke endpoint was replaced
with the existing HTTPS route backed by `monitoring/scrutiny:8080`. The
collector is now reproducibly declared under `stacks/monitoring/nas`, retaining
its pinned image, `choms-nas` identity, five-device discovery, privileges,
mounts, bridge network and six-hour schedule. Its normal startup collection
refreshed the same five records without duplicates or publication errors;
Scrutiny remained healthy and RAID/NFS were unchanged.

On 2026-08-29 actionable NAS, Kubernetes-node and storage monitoring was
completed. One digest-pinned, non-privileged node-exporter on `choms-nas`
exposes only filesystem, diskstats, hwmon, mdadm and atomic textfile metrics to
the private Prometheus target labeled `instance=choms-nas, role=nas`. An
unprivileged persistent user timer summarizes NFS, mdmonitor, RAID and Scrutiny
freshness every minute; `Linger=yes` preserves it across reboot. Thirteen
CHOMS rules add only persistent actionable critical conditions while reusing
upstream critical filesystem/PVC rules. Controlled synthetic FIRING and
RESOLVED delivery reached Telegram. Final state had target UP, no CHOMS alert,
Prometheus/Alertmanager 1/1, RAID `[UUUU]`, active NFS and fresh five-device
Scrutiny ingestion. SMART failure prediction and kernel-log errors remain
explicit gaps rather than inferred metrics.

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
- External runtime Secrets do not have a verified independent recovery copy.
- Several application PVCs and node-local state paths remain outside the
  versioned backup system despite the successful central database restore.
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

## Raspberry Pi external monitor — Phase 1

The US Raspberry Pi 3 runs one approximately 15.6 MiB ARMv7 container that
performs anonymous DNS, HTTPS, TLS-expiry, expected-status and latency checks
for the main endpoint, a public Nextcloud route and an Authelia-protected
route. A non-privileged user service supplies only microSD capacity/inodes,
host-root mount state, temperature, firmware throttling flags and the
exact-name running state of `firefox-web`; the Docker socket is not mounted.
Alert state persists outside the container and sends one Telegram FIRING after
three consecutive failures and one RESOLVED on recovery. Bot token and chat ID
are independent RP3-local mode-0600 files ignored by Git and rotated with the
interactive installation script.

Observed HTTP behavior is declared as Nextcloud `302` to its login and
protected Home `302` to `auth.chomsmaster.com`. An explicit non-following HTTP
client corrected the initial Home behavior. A false read-only signal came from
the helper's `ProtectSystem=strict` namespace; it now reads the PID 1 mount
namespace and confirms the host root is read-write. The RP3 kernel cannot
enforce the declared Compose memory limit, although the conservative
declaration and the CPU/PID/read-only/capability controls remain.

The monitor is healthy with zero restarts. Both HTTP alerts and the read-only
signal are resolved, but `rp3-local` correctly remains firing for `0x50005`:
undervoltage and throttling are current and have also occurred since boot. Use
a known-good regulated 5.1 V / 2.5 A supply and a short, low-resistance
micro-USB cable. Do not reboot merely to clear evidence; first stabilize power.
Current bits should then disappear and the alert should resolve automatically.
Historical bits require a later controlled reboot after the physical repair.


## 2026-10-23 — Fase 1: validación local y CI

Preparado un punto único scripts/validate.sh y CI con versiones fijadas. Validación final pendiente; sin consultas ni cambios en producción. Herramientas ausentes se informan; CI falla si la suite queda incompleta.


## 2026-10-23 — Fase 2: NetworkPolicies propuestas

Preparadas 13 carpetas con deny y excepciones, matriz de puertos y rollout explícito por namespace desde Colegio. No aplicado; labels Helm, CNI, DNAT y pruebas de conectividad pendientes. Véase docs/operations/NETWORK_POLICIES.md.


## 2026-10-23 — Fase 3: IaC de adopción y offsite

Preparados providers Kubernetes/Helm fijados, imports de 13 namespaces públicos/6 releases, entorno AWS independiente y módulo almacenamiento cloud retirado cifrado/versionado en eu-central-2. Sin import, plan, apply, estado o credenciales. Retención Restic separada del lifecycle almacenamiento cloud retirado; restauración offsite pendiente.


## 2026-10-23 — Fase 4: higiene declarativa

Cron Moodle: historial success=1/fail=2 y TTL de Job 86400 s. Digest speaker existente conservado, coherencia registry/imageID con v0.15.2 pendiente; no se repite su rollout bloqueado. Runbooks de limpieza y digests pendientes añadidos. Ningún Pod/PV/PVC modificado ni eliminado.


## 2026-10-23 — Fase 5: presentación y evidencia

README compacto en inglés, baseline fechado y nodos/topología reconciliados con el inventario; auditoría antigua marcada como histórica. Lista pública pendiente de decisiones del propietario, sin eliminar servicios/archivos. Validación final todavía pendiente. Sin acceso a producción ni secretos/estado.


## 2026-10-23 — Cierre local: dos validaciones, aceptación pendiente

Cinco fases de código/documentación preparadas en feature/devops-hardening,
sin push. Validación 2: yamllint, seis helm lint, Bash/ShellCheck, Gitleaks y
terraform fmt/validate (tres directorios) PASS. NetworkPolicies 126/126 válidas;
general 222 válidos/35 sin schema omitidos. Trivy FAIL con 62 hallazgos
(61 HIGH/1 CRITICAL), incluido cifrado del diseño retirado frente a CMK en módulo nuevo. CI no verde:
resolver hallazgos o revisar excepciones por recurso; no se han silenciado.
No hay adopción, despliegue, consultas a producción, lectura/escritura de
Secret values, kubeconfig ni tfstate. Runtime, CNI, imports, offsite y restauración
siguen pendientes de aceptación del propietario. Sin tercera validación.


## Encargo local — kit de recuperación y seguridad informativa

Retirados módulo y entorno de infraestructura externa y su documento; referencias
previas ajustadas por petición explícita, sin reescribir historial Git. Preparados
RECOVERY_KIT.md, exportador offline SOPS/age de allowlist cerrada y REBUILD_RUNBOOK.md.
El exportador NO se ejecutó; no se creó/inspeccionó el repo privado ni se leyó
ninguna clave, Secret, kubeconfig o estado. Kit sin datos de aplicaciones.
Trivy pasa a informativo; backlog de referencia 61 (1 CRITICAL/60 HIGH).
No se cambia ningún manifiesto para endurecerlo. Plan privado de servicios de
ocio: 4 archivos exclusivos, 18 compartidos y 17 documentos, sin mover ni borrar
esos servicios y sin ejecutar filter-repo. Validación única pendiente al cierre.


### Cierre del encargo de recuperación

Validación única: exit 0, sin herramientas/charts omitidos. Sintaxis/ShellCheck
del exportador PASS; seis charts, Terraform homelab y Gitleaks PASS. Políticas
126/126; conjunto general 222 válidos y 35 sin schema omitidos. Trivy informa
61 hallazgos (1 CRITICAL, 60 HIGH), sin bloquear. Exportación, clave/inputs reales,
restauración, repo privado y filter-repo NO ejecutados/inspeccionados. No hay
cambios de manifiestos ni de producción. Se conserva la rama local sin push.


## Separación local del alcance público

Extensiones específicas conservadas con rutas relativas y SHA-256 en repositorio
hermano local sin remoto. Copias originales preservadas antes del saneado de
referencias compartidas; seis rutas de revisión/específicas retiradas del árbol
público solo después de verificar. Sin cambios runtime, commits, publicación
ni reescritura de historial. La comprobación final es local y acotada.

## Estado de recuperación offline — 24-10-2026

Exportador genérico solo con recipient público age, selección cerrada y salida
atómica verificable. Véase [contrato](../operations/RECOVERY_KIT.md). Kit real,
restauración real y publicación siguen pendientes; sin cambios de producción.
Pruebas exclusivamente sintéticas; la política del destino se revisará aparte.

## OmniRoute — 25-10-2026

Preparación acotada de gateway privado API-key en namespace independiente,
release oficial v3.8.52 y Redis separado, ambos por digest. Estado de ejecución
y aceptación en [runbook](../operations/OMNIROUTE.md). No se configuran proveedores
ni se prueban modelos; backup independiente y restore quedan pendientes.

Cierre de este intento: NO desplegado; preflight detenido por comprobación de
ruta protegida existente. Sin escrituras live, Secrets generados ni rollout de
Authelia. Los manifiestos quedan preparados sin commit/push; resolver primero
el bloqueo de autenticación observado antes de autorizar una continuación.


## 2026-10-25 — cert-manager DNS aplicado; OmniRoute detenido

Un Pod diagnóstico temporal sin privilegios en cert-manager verificó
1.1.1.1/1.0.0.1 por UDP/TCP 53 y se eliminó. No hay NetworkPolicies en ese
namespace. Values Helm añaden únicamente el override de nameservers HTTP-01;
chart v1.21.1 conservado. El render comparó 51 objetos con la release/hooks:
solo un argumento del controller cambia; rollback del argumento reproduce la
baseline. Flujo versionado filtrado a cert-manager, sin actualizar otras releases.
Controller/webhook/cainjector 1/1 Ready; flag exactamente una vez; CoreDNS intacto.

Único reintento: Challenge valid, Order valid y Certificate Ready, SAN OmniRoute
y cobertura anterior conservados. Se validó y aplicó la regla exacta Authelia,
un rollout y contratos Home/Prometheus/Grafana correctos; OmniRoute/Redis Ready
en node-02 y dashboard 302 a Authelia. La verificación final falló con una
aserción sin checkpoint detallado: causa concreta no recuperada, no se declara
un defecto de aplicación ni aceptación operacional. Rollback del servicio:
réplicas 0, rutas/regla/SAN retirados; datos y Secrets preservados. Corrección
DNS permanece aplicada. Helper pendiente, sin proveedores, inferencia ni
commit/push. Ver [runbook](../operations/OMNIROUTE.md).


## 2026-10-25 — OmniRoute activo; API privada y túnel demostrados

Corrección explícita de los estados detenidos anteriores: la política del API
permitía un origen CNI distinto del seleccionado por node-01. Se sustituyó solo
10.42.0.1/32 por 10.42.0.0/32, preservando LAN /32, selector y TCP/20129; validación
estructural, dry-run servidor y diff limitado antes de aplicar. Después, PodIP y
ClusterIP desde node-01 devolvieron 401 sin clave. Túnel temporal loopback desde
node-dev-01 también devolvió 401 y se cerró; helper bash -n/ShellCheck PASS.

Sin reescalar de nuevo: SAN Ready preservando cobertura anterior, regla exacta
Authelia validada y un rollout controlado, dashboard/administración solo 20128.
Checks nombrados PASS: Home/Prometheus 302 a Authelia, Grafana 302 /login,
dashboard 302 a Authelia; /v1 público 404 sin regla backend coincidente; API solo
ClusterIP:20129. Ambos workloads 1/1 Ready en choms-node-02, cero reinicios,
digests declarados, PVC Bound y PV Retain/afinidad node-02; endpoints Ready.
Se mantienen activos. cert-manager/CoreDNS no se modificaron en este cierre.

Backup independiente, restore controlado, alta Kuma y matriz negativa completa
de NetworkPolicies siguen pendientes. No se leyeron claves ni cuerpos HTTP,
no se configuraron proveedores ni se hicieron inferencias. Validación local
final en una pasada al cierre; resultado en el informe. Sin commit ni push.
Véase [operación y rollback](../operations/OMNIROUTE.md).


## 2026-10-25 — Cierre en Git de OmniRoute

Helper de túnel versionado sin IP fija: destino SSH obligatorio, descubrimiento
del ClusterIP por kubectl de solo lectura, validación IPv4 y bind loopback.
Ejecución foreground y cierre con Ctrl+C; sin credenciales. Pruebas del helper
exclusivamente sintéticas; no se reabre el túnel ni se repiten rollouts.
Cierre autorizado mediante un commit lógico y push normal tras fetch, revisión
de alcance/sensibilidad y confirmación declarativa/live de solo lectura.
Backup/restore, monitor Kuma y matriz negativa de aislamiento siguen pendientes.


## 2026-10-25 — Memoria local instalada; gates K3s abiertos

Codebase Memory nativo v0.12.1, checksum y firma Sigstore verificados, instalado
sin sudo/configurador automático. Índice privado de la única raíz pública,
allowlist exacta y exclusiones; sin UI, hooks, watchers o subagentes. Entradas
MCP Codex/Claude con backups privados; handshake y búsquedas estructurales PASS
por sus configuraciones, sin ejecutar modelos. Evidencia y límites de cobertura
en [runbook de memoria](../operations/MEMORY_PLATFORM.md).

Precheck agrupado main/c1af248 limpio y sincronizado; OmniRoute sano. Node-02
seleccionado preliminarmente por RAM/disco frente a node-03, sin usar node-01
para persistencia. Ningún recurso K3s nuevo aplicado: chart OpenHands v1.33.0
comparte Pod/PVC y no satisface sandbox por conversación. Cognee sin ingesta
mientras se aclara la prohibición de inferencias locales; imagen MCP de release
no disponible y candidato por commit sin aceptación de compatibilidad/auth.
Sin claves o fallbacks de proveedores, inferencias, commit o push. Se conserva
el componente local operativo; gates K3s/restore/aislamiento siguen pendientes.


### Validación del bloque local de memoria

Admisión/restore artificial, persistencia, alta/baja de símbolo sintético y
MCP por las dos configuraciones comprobados. La única pasada del validador
detectó SC1091 en el helper con source; quedó autocontenido y pasó bash -n,
ShellCheck --norc y diez fixtures sin SSH. YAML/Python y Gitleaks pasaron; no se
repitió la suite general. Los intentos del harness se corrigieron sin atribuir
sus fallos de formato al indexador. Los gates K3s siguen abiertos, sin commit.


## 2026-10-25 — Corrección de estado: modelos locales autorizados; gate offline fallido

FastEmbed y GLiNER exclusivamente locales están autorizados. Sustituye la
aclaración pendiente anterior; OpenHands sigue expresamente aplazado y su
chart v1.33.0 no cumple sandbox independiente por conversación.

Se descargaron una sola vez los archivos fijados de ambos modelos: 849.893.045
bytes de contenido, fuera de Git. Revisiones, tamaños y hashes de procedencia
en `docs/architecture/memory/models-lock.json`; SHA-256 por archivo en el
manifiesto privado local del cache. No se descargaron pesos de proveedores ni
se configuraron claves. FastEmbed produjo un vector de 384 dimensiones sobre
un fixture artificial en un contenedor sin red.

`CHECK_FAIL local_models_offline`: GLiNER2 2.1.0 / Transformers 4.57.6,
incluidos en la imagen Cognee 1.6.5 fijada, fallaron al cargar el tokenizer.
Primero `extra_special_tokens` como lista produce AttributeError; el fallback
interno termina en JSONDecodeError. Los JSON descargados sí parsean y sus
hashes Git blob coinciden con los oficiales: no atribuirlo a descarga corrupta
ni afirmar determinada la causa del segundo error. No se cambian dependencias
ni se modifican pesos/tokenizer para ocultarlo.

Manifiestos API/PostgreSQL preparados, sin aplicar ni aceptar como validados
live. No se creó namespace, PVC, Secret, Pod o listener K3s; no se necesita
rollback. Tampoco ingesta, consulta de aceptación, reinicio, restore PostgreSQL
o pruebas MCP. Se conserva Codebase Memory; no se repitieron sus pruebas.
MCP continúa pendiente de procedencia completa/compatibilidad/auth de entrada.
No hubo llamadas a OmniRoute/cloud, proveedores, commit o push. El pico real
CPU/RAM del intento fallido no quedó medido; los límites no son mediciones.


### 2026-10-25 — Gate offline: etapas Python PASS, proceso nativo FAIL

Corrección explícita: la matriz con snapshot local cargó tokenizer/AutoExtractor
y extrajo entidades artificiales sin red, pero Docker terminó con exit 139 y
`munmap_chunk(): invalid pointer` durante el cierre nativo. El PASS del JSON
antes del cierre no acredita el proceso completo. Biblioteca responsable no
determinada; no se cambian dependencias ni se repite la matriz.

Runtime Python 3.12.14: Cognee 1.6.5, GLiNER2 2.1.0, Transformers 4.57.6,
tokenizers 0.22.2, huggingface-hub 0.36.2, protobuf 7.36.2,
sentencepiece 0.2.2 y Torch 2.14.1+cpu. El lock oficial v1.6.5 fija GLiNER2
2.0.0 y Torch 2.14.0; el resto coincide. No se atribuye el crash a una de esas
diferencias sin evidencia. No se actualizó a Transformers 5.

Las dos excepciones históricas completas, sanitizadas, el inventario de
snapshot y sus hashes están en `docs/architecture/memory/offline-gate.json`.
Primaria: transformers `_set_model_specific_special_tokens`, AttributeError
por metadatos legacy list-valued. Fallback: transformers `_from_pretrained`
llama `json.load`, JSONDecodeError; no se reprodujo con snapshot local directo.
Los archivos JSON presentes son válidos; spm.model/special_tokens_map.json/
added_tokens.json no estaban en el snapshot preparado ni fueron necesarios
para cargarlo. No se descargaron otros modelos ni pesos.

Se inició la reanudación al leer prematuramente el PASS Python: PostgreSQL ya
estaba sano cuando se detectó el fallo nativo. Orquestador detenido, Pod temporal
de precarga eliminado; PostgreSQL conservado. API/MCP no creados. Los dos PVC
Bound y ambos Secrets runtime se preservan; la transferencia de modelos al PVC
quedó interrumpida y no está aceptada. No hubo ingesta, restore, reinicios de
aceptación ni consulta OmniRoute. OpenHands sigue aplazado por aislamiento.

Medición sintética: 9,332 s, CPU 10,165 s y RSS máximo 2.178.836 KiB; no son
mediciones de servicio K3s ni ahorro de tokens. Hash de pesos sin cambios.
Sin proveedores, inferencia generativa, cambios a servicios ajenos, commit o
push. El siguiente trabajo debe aislar el crash nativo antes de aplicar API.


### 2026-10-25 — Runtime frozen: gate local PASS; distribución pendiente

Fuente oficial v1.6.5, commit `37f788bd287750e10d7610173e5332b3843f6ebd`:
firma GPG verificada y árbol del archivo fuente idéntico al árbol firmado.
Build exclusivo `uv sync --frozen`, sin instalador posterior GLiNER. Imagen
final y receta fijadas en `docs/architecture/memory/release-lock.json`.

Python 3.12.12, Cognee 1.6.5, GLiNER2 2.0.0, Torch 2.14.0,
Transformers 4.57.6, Tokenizers 0.22.2, HuggingFace Hub 0.36.2,
SentencePiece 0.2.2 y Protobuf 7.36.2. Dos smoke tests autorizados: runtime
frozen y su imagen final, ambos exit 0 tras cierre normal del intérprete,
sin diagnósticos de allocator. Modelo read-only, sin red, hashes intactos;
no se repitieron FastEmbed/Codebase/MCP ni descarga de pesos.

Imagen final: tres entidades esperadas, 8,645 s de proceso, CPU 8,741 s,
RSS máximo 2.526.940 KiB. Se clasifica el fallo anterior como incompatibilidad
del runtime no bloqueado, sin atribuir culpabilidad a un paquete individual.
Se conserva la evidencia anterior, incluido exit 139; stderr completo retenido.

API aún ausente: node-02 requiere privilegios para importar la imagen local y
sudo no interactivo no está autorizado. No se pidió contraseña, cambió permisos,
publicó imagen en un registry o aplicó ningún recurso K3s en esta ejecución.
PostgreSQL, PVC/PV y Secrets conservados; MCP/OpenHands bloqueados. Precarga
atómica y rollout API pendientes de importación; no reutilizar la copia parcial
anterior del volumen de modelos. Sin commit ni push.


### 2026-10-25 — Precarga detenida: ErrImageNeverPull

Importación aceptada por confirmación autoritativa del operador: tag/digest
fijados, linux/amd64 y CRI_MANAGED=true. No se repitió Node.status.images,
importación, build, gate offline ni preflight. El manifiesto ya fija el digest,
imagePullPolicy Never y nodeSelector exclusivo choms-node-02.

El Pod temporal de precarga llegó a Pending en node-02 con ErrImageNeverPull
para la referencia por digest. Falló la etapa `atomic_seed_pod_ready`: no llegó
a ejecutarse transferencia, verificación de pesos, rename, API ni ingesta.
Se interrumpió la espera al constatar el error; KeyboardInterrupt del harness
no es la causa del fallo. No se atribuye el error a GLiNER ni al gate offline,
que sigue PASS. La resolución exacta de la referencia en CRI queda pendiente;
la evidencia no invalida la confirmación de importación del operador.

Rollback único: Pod temporal eliminado y ausencia comprobada. PostgreSQL Ready,
ambos PVC Bound y Secrets existentes conservados por nombre. API ausente; sin
modelos modificados ni nuevos modelos publicados. MCP/OpenHands no desplegados.
Autenticación, consulta trazable, persistencia y restore no se ejecutaron.
Sin inferencias, proveedores, commit o push.


### 2026-10-25 — Tag local resuelto; validación imageID detenida

Se cambió únicamente la referencia declarativa API al tag local exacto
`docker.io/library/choms-cognee-frozen:1.6.5`, conservando Never y node-02.
La correspondencia del tag con el digest a90ce0eb… se aceptó de la confirmación
autoritativa del operador, sin repetir build, importación o gate offline.

El Pod temporal arrancó Ready en choms-node-02: ErrImageNeverPull queda
superado mediante el tag. Falló `temporary_seed_imageid_exact_digest`: la
aserción exigida de que imageID contenga el digest del índice devolvió false.
El verificador no conservó el valor observado antes del rollback; no se inventa
ese valor ni se concluye que se ejecutara una imagen incorrecta. Causa pendiente.

Rollback original único: Pod temporal eliminado, ausencia confirmada y
PostgreSQL Ready. Transferencia no iniciada, modelos sin modificar, API no
aplicada; PVC/PV, Secrets e imagen preservados. No se ejecutaron ingesta,
consulta, persistencia o restore; MCP/OpenHands siguen sin desplegar.
Sin reinicios ajenos, proveedores, inferencias, commit o push.


### 2026-10-25 — Corrección de configuración y único intento API Cognee

Corrección explícita del estado anterior: la precarga atómica ya terminó con
hashes verificados y publicó `models-5e3cf446963b6c90`; el Pod temporal fue eliminado.
El imageID CRI se conserva como evidencia y no se compara textualmente con el índice OCI.

La validación sintética, sin red y dentro de la imagen fijada, demostró que
`DEFAULT_USER_EMAIL` con dominio `.invalid` falla en el campo `email` (`EmailStr`,
`BaseUserCreate`/`InternalUserCreate`): el dominio está reservado. Se corrigió
únicamente a `choms-memory@example.com`; no se modificó ninguna credencial.
YAML/Python, dry-run servidor y diff acotado pasaron: solo cambió el correo del
ConfigMap y las réplicas del Deployment de 0 a 1.

El único intento API posterior no alcanzó Ready en 360 segundos, con cero
reinicios. Los logs sanitizados sitúan el nuevo bloqueo en
`health.check_vector_db` → `FastembedEmbeddingEngine.get_tokenizer`, con
`SSLError`, `ClosedPoolError` y `OSError` durante carga/fallback del tokenizer.
No se ejecutó ingesta ni se descargaron modelos. El ValidationError no se
observó en este intento; autenticación y aceptación siguen sin acreditar.

Evidencia sanitizada preservada antes del rollback único; API devuelta a cero.
PostgreSQL, PVC/PV, Secrets, imagen y modelos validados se preservan. Pendientes:
resolver carga offline del tokenizer usada por health y, después, autenticación,
ingesta trazable, persistencia y restore. MCP bloqueado; OpenHands aplazado.
Sin build, importación, nueva precarga, proveedores, inferencias, commit o push.


### 2026-10-25 — Tokenizer BAAI offline PASS; ingesta detenida antes de add

Se fijó BAAI/bge-small-en-v1.5 en la revisión
`5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`, únicamente para tokenizer.
El hash Git oficial de tokenizer.json coincide con Qdrant: se reutilizaron sus
711396 bytes. Se adquirieron solo tokenizer_config.json, special_tokens_map.json
y vocab.txt (231999 bytes en total); sin pesos BAAI ni config.json.
Revisión, tamaños y SHA-256 están en models-lock.json.

Nuevo conjunto publicado atómicamente tras verificar todos los hashes:
`models-76fb6636f317812a`; `models-5e3cf446963b6c90` permanece intacto.
La prueba exacta get_tokenizer en la imagen fijada, UID 1000 y PVC existente
terminó con código 0, caché BAAI encontrada, cero excepciones, cero intentos de
conexión y sin fallback TikToken. El Pod temporal fue eliminado; el wait de
eliminación venció, pero una lectura posterior confirmó su ausencia.

Único rollout API: Ready en choms-node-02, cero reinicios; imageID CRI
`sha256:268be24f6cd9881d1e0589d74b33950bbe69715fcbb21ae9444b695c768db3f2`.
Autenticación nativa probada: 401 sin credencial y 200 autenticado; solo ClusterIP,
sin HTTPRoute ni Ingress. No se mostraron credenciales.

Gate siguiente falló antes de cognee.add: al importar LiteLLM,
get_model_cost_map intentó HTTP para metadatos; la guarda del proceso de
aceptación rechazó la solicitud antes de enviarla. No se ejecutaron inferencias
ni se añadieron documentos al dataset. Se materializaron únicamente 36 fuentes
públicas admitidas (335712 bytes) en el directorio de importación del PVC.
Evidencia sanitizada conservada antes del rollback único: API a cero réplicas;
la declaración mantiene una réplica para el próximo intento autorizado.
PostgreSQL, PVC/PV, Secrets, imagen y ambos conjuntos validados se preservan.
Pendientes: importación LiteLLM sin HTTP, ingesta/consulta trazable, persistencia
y restore. MCP bloqueado, OpenHands aplazado. Sin commit ni push.


### 2026-10-25 — LiteLLM local PASS; add detenido por HTTP del tokenizer

La imagen fijada contiene LiteLLM 1.105.0. Su get_model_cost_map implementa
LITELLM_LOCAL_MODEL_COST_MAP; no se encontró implementación de
LITELLM_OFFLINE_MODE y no se añadió esa variable. Se declaró únicamente
`LITELLM_LOCAL_MODEL_COST_MAP: 'True'` antes de importar Python.
Prueba efímera, UID 1000, red none y guardas de sockets/HTTP: código 0,
mapa empaquetado local con 4459 entradas, URL nula y cero intentos de red.
No se descargó ni sustituyó el mapa.

Dry-run y diff acotados: solo la variable demostrada y réplicas 0 a 1.
Único rollout: Ready en choms-node-02, cero reinicios, imageID CRI registrado;
401 anónimo y 200 autenticado, sin imprimir credenciales. ClusterIP únicamente.

Al continuar cognee.add, falló public_corpus_add: resolve_embedding_tokenizer
intentó HTTP hacia los archivos tokenizer.json/tokenizer_config.json de BAAI
y el fallback TikToken hacia cl100k_base.tiktoken. Las tres solicitudes fueron
rechazadas por la guarda antes de enviarse; no fue get_model_cost_map.
URLs sanitizadas, módulos y frames quedaron conservados antes del rollback
único. La ingesta no terminó; posible estado parcial del dataset no verificado
ni eliminado. No se ejecutaron consulta, reinicio/persistencia o restore.

API a cero tras rollback. PostgreSQL, PVC/PV, Secrets, imagen y
models-76fb6636f317812a preservados. Sin cambios a modelos, probes o políticas;
sin inferencias generativas, MCP, OpenHands, commit ni push. El siguiente bloque
debe explicar la resolución del tokenizer en el contexto de cognee.add sin
repetir ni invalidar el gate de carga offline ya aprobado.


### 2026-10-25 — Ruta local FastEmbed: parche probado, imagen pendiente

Se demostró que HUGGINGFACE_TOKENIZER llega a create_embedding_engine, pero
no se propaga a FastEmbed; su resolver ignora el argumento local y permite
fallback TikToken. Prueba original: código 1, snapshot presente y red bloqueada.
Parche mínimo de cuatro archivos, sobre fuente oficial verificada, preparado en
stacks/kubernetes/choms-memory/patches/cognee-1.6.5-local-tokenizer.patch.
Diez regresiones offline PASS con código 0 y cero intentos de red, mediante
mounts explícitos de fuente revisada en la misma imagen, UID 1000/network none.
FastEmbed permanece; tokenizer local_files_only=True, sin fallback en el perfil
local explícito. Sin monkeypatch de implementación ni sitecustomize.

API sigue a cero: no se construyó imagen ni se aplicó variable/rollout.
Consulta READ ONLY del dataset exacto: 1 dataset, 0 filas en data; fragmentos
vectoriales/grafo no verificados. No hubo borrado ni reingesta. La limpieza
mediante API soportada debe preceder a cualquier futura ingesta, después de
admitir la imagen corregida. Detalle en docs/operations/COGNEE_LOCAL_TOKENIZER_PATCH.md.
PostgreSQL, PVC/PV, Secrets, imagen y models-76fb6636f317812a sin modificar.
Sin MCP, OpenHands, commit ni push; resto de la aceptación sigue pendiente.


### 2026-10-25 — Imagen derivada validada; importación de operador pendiente

Una sola construcción desde la base local Cognee 1.6.5 confirmada. Parche
SHA-256 `204a2a7e1d17b20c21d43a6f83cec2e45d7b09351444cc2c5b6189532d24e7f2`. Aplicación fuzz=0 con hashes originales y finales;
la capa OCI nueva contiene exactamente los cuatro archivos aprobados.
Sin cambios a dependencias, uv.lock, Cognee, LiteLLM, Torch o modelos.

Tag preparado: `docker.io/library/choms-cognee-local-tokenizer:1.6.5-p204a2a7e1d17`.
Índice OCI: `sha256:b9c82ac89e7eaed83fc01e9a620e51dab7a97d994925b675e3785998395cef6c`.
Manifest linux/amd64: `sha256:a57317edb1aef8c3a1ae2377b0e52c37f8eb62a5bb99691709192f97a9ec7bc1`.
Diez regresiones dentro de la imagen final: PASS/código 0; sintaxis, imports
Cognee/LiteLLM y mapa empaquetado offline: PASS. Sin mounts de código parcheado
en estas pruebas finales. Guarda de auditoría: cero conexiones de red.

Smoke cognee.add: PASS/código 0, un dataset y una fila sintéticos. Backend
relacional SQLite, vector LanceDB y grafo Kuzu, todos desechables; no es una
nueva validación de PostgreSQL. No se ejecutó cognify ni se ingirió el repo.
Duración del smoke: 13.76 s;
CPU 14.779 s; RSS máximo
1319564 KiB. Se corrigieron solo dos restricciones
del harness: montaje anidado sobre caché read-only y raíz read-only incompatible
con la creación de directorios de extensiones Ladybug. Modelo read-only y red
none se conservaron. El filesystem efímero escribible reproduce el Deployment.

Artefacto persistente en
`~/.local/share/choms-memory/images/cognee-1.6.5-local-tokenizer-p204a2a7e1d17/image.tar`.
3714351104 bytes; SHA-256 antes/después:
`f9cd80cf1e2737d29feadc841cb640e3bf293fb2b7e5904da53a1b3f57199d37`. Directorio 0700, archivos 0600.
Metadatos, checksums y script de operador preservados junto al tar.

Importador preparado, **NO EJECUTADO**:
`/tmp/choms-import-cognee-local-tokenizer-node02.sh`.
SHA-256: `fae079157c58b8c037c682eb733c2071fbbe35a57ea7b03ff0ae2b501f949c41`. Comprueba usuario, hostname, espacio, hash local/remoto,
strict host checking, un solo sudo visible, importación/digest/CRI con k3s ctr;
elimina tar remoto únicamente tras éxito y preserva siempre el artefacto local.

Manifiestos actualizados al nuevo tag local con Never y node-02; ruta
HUGGINGFACE_TOKENIZER explícita al snapshot de models-76fb6636f317812a.
**No aplicados**: API sigue a cero. No hubo SSH, importación ni cambios live.
El registro de dataset existente se conserva. Después del futuro rollout:
verificar dataset/data/vector/grafo y eliminar solo ese dataset mediante API
soportada antes de reingestar; nunca limpieza directa de PostgreSQL o volúmenes.
No se anticipa aceptación completa API/ingesta/consulta/persistencia/restore.
Sin MCP, OpenHands, commit, push ni publicación en registry.


### 2026-10-25 — API parcheada Ready; rollback indebido por contrato del verificador

Importación confirmada por operador: tag local parcheado, índice OCI b9c82ac8…,
CRI_MANAGED y artefacto local preservado. No se repitió importación ni build.
Único rollout autorizado: Ready en choms-node-02, cero reinicios, Never y uso
local sin descarga. imageID observado: sha256:a56ec10ad5624ffdfccc8dc6de7f14c857914001c4ba8c68b4dabcd1acc51df9.
Autenticación: 401 anónimo, 200 autorizado; solo ClusterIP.

Inspección READ ONLY del dataset choms-homelab-public: UUID
94debd98-e646-511c-91e8-41cf6f0cea25, creado a las 14:31:00.705528 UTC;
cero filas data y ningún binding dataset_database. No se ejecutó DELETE.
La inspección física vector/grafo y la ausencia posterior de fragmentos siguen
pendientes; no se afirma que esa comprobación haya terminado.

El endpoint /health devolvió 200 y status=ready. El verificador asumió
incorrectamente que este resumen incluía components (corresponde a /health/detailed)
y ordenó un rollback indebido antes de tocar el dataset. No hay un fallo de
Cognee demostrado. Se conserva evidencia clasificada VERIFIER_DEFECT.
La función del contrato fue corregida y pasó ocho casos sintéticos locales.

API quedó a cero por ese error. No se realizó un segundo rollout porque la
instrucción vigente autorizaba uno único. Se requiere ampliación explícita de
ese límite para reactivar y continuar la aceptación. PostgreSQL, PVC/PV, Secrets,
imagen, modelos y dataset se preservan. Sin ingesta, restore, MCP, OpenHands,
Hermes, ECC, commit o push en este bloque. No se mostraron credenciales.

### 2026-10-25 — Reactivación adicional: add completado; cognify bloqueado por OOM

La reactivación adicional autorizada pasó readiness (HTTP 200, status=ready),
autenticación 401/200, node-02, cero reinicios iniciales e imagen local Never.
El contrato no exige campos opcionales de /health. El dataset vacío anterior
se eliminó mediante la API soportada tras comprobar ausencia de fragmentos.
El fixture sintético se añadió, se verificó byte a byte y se eliminó; su primer
DELETE encontró un bloqueo de grafo del cliente SDK aún abierto. Tras cerrar
ese proceso, DELETE terminó correctamente y no quedaron fragmentos del fixture.

La ingesta admitió 36 documentos públicos (373600 bytes): add_pipeline quedó
DATASET_PROCESSING_COMPLETED. Durante local_gliner_cognify, el contenedor
terminó a las 16:08:37 UTC con reason=OOMKilled, exitCode=137 y un reinicio.
Los contadores leídos después del reinicio correspondían al contenedor nuevo;
su valor cero no descarta el OOM del anterior. No se atribuye a un paquete
concreto ni se afirma una causa más detallada del consumo de memoria.
Cognify quedó DATASET_PROCESSING_STARTED: no se acepta como índice terminado.

Se conservó evidencia sanitizada antes del rollback único: solo API a cero,
sin Pods API restantes; PostgreSQL continúa 1 Ready y ambos PVC Bound.
PVC/PV, Secrets, imagen, modelos y los 36 documentos se preservan; no hubo
limpieza directa de PostgreSQL ni reingesta. No se modificaron otros servicios.
La guarda registró cero salidas no autorizadas en las etapas que terminaron;
el proceso interrumpido no emitió su informe final de conexiones y no se
certifica ese contador. Las NetworkPolicies de salida permanecen sin ampliar.

Pendientes: diagnóstico acotado de memoria en cognify, consulta trazable,
reinicio/persistencia y backup/restore controlado. No reactivar sin autorización
ni borrar el dataset parcial automáticamente. MCP continúa bloqueado y
OpenHands aplazado. Sin proveedores, inferencia generativa, commit o push.

### 2026-10-25 — Gate RAM: límite de contenedor confirmado; intento único a 8 GiB fallido

Diagnóstico acotado: request/limit anteriores 2/6 GiB; límite cgroup efectivo
6 GiB y lastState OOMKilled/137 conservado. Node-02 tiene 23,37 GiB allocatable,
MemoryPressure=False y 18,36 GiB disponibles en la lectura previa. Prometheus
conserva un máximo muestreado de 1,84 GiB en la ventana anterior: no captura
el pico fatal y no sirve para dimensionar por sí solo.

Se ajustaron exclusivamente requests.memory=6Gi y limits.memory=8Gi, manteniendo
CPU, imagen, modelos, probes, Secrets, políticas y nodo. Es una estimación,
no un pico demostrado: presupuesto aproximado 6,2 GiB para GLiNER y procesos
Cognee/FastEmbed con ~29 % de margen hasta 8 GiB. Tras requests quedan 13,66 GiB
allocatable sin reservar. YAML, dry-run servidor y diff exacto pasaron; el único
cambio adicional live fue la reactivación autorizada 0 -> 1.

Los 36 documentos anteriores se identificaron por ruta, commit y SHA-256.
Había binding, base vectorial y archivos de grafo. Al no garantizarse replay
atómico tras crash, se eliminó exclusivamente ese dataset mediante la API
soportada (200), verificando ausencia de todos sus fragmentos antes de add.
No se repitió el fixture sintético ni se modificó PostgreSQL directamente.

Único intento: API Ready en node-02, Never/local sin descarga y 401/200;
add precedió a local_gliner_cognify. Se guardaron 57 muestras durante 555 s,
con memory.peak=8589934592 bytes (8 GiB). A las 16:33:44 UTC el contenedor
terminó OOMKilled/137 y registró un reinicio; MemoryPressure siguió False.
El pico está truncado por el límite: la necesidad real es mayor o igual a 8 GiB,
no un valor superior medido. Clasificación: container_limit_exceeded.
Los contadores cero del contenedor nuevo no representan el contenedor muerto.

Evidencia conservada antes del rollback único de API a cero, sin Pods API
restantes. PostgreSQL sigue 1 Ready; ambos PVC Bound y ambos Secrets por nombre
preservados. Se conservan PV, imagen, modelos y dataset parcial para inspección
posterior. No se aumenta de nuevo el límite ni se reintenta cognify en este bloque.
La guarda de red estaba activa, pero el SIGKILL impidió emitir el contador final:
cero salidas automáticas no queda certificado; políticas no ampliadas.

Gate RAM/cognify FAIL. Consulta trazable, persistencia, restore y MCP no ejecutados.
Como referencia para una futura decisión, 8 GiB +25 % =10 GiB; sigue siendo
un mínimo estimado con pico censurado, no una garantía ni un cambio autorizado
ya aplicado. Sin ampliación hardware, swap, otros servicios, commit o push.
Evidencia pública sanitizada: docs/architecture/memory/memory-gate.json.

### 2026-10-25 — Backup Cognee preparado; ejecución bloqueada antes de capturar

Base 11d9150. Se identificaron por metadata las dos bases (relacional y
pgvector por dataset), grafo Ladybug/kuzu, documentos, modelos publicados,
fuente/locks/parche e imagen OCI preservada. Sin dumps ni copias live.
Restic root-only en node-01 requiere sudo interactivo; no se solicitó ni leyó
la contraseña. El dataset_lock de Cognee es local al proceso y no constituye
una barrera de captura entre stores. No se copiará el grafo abierto ni se
forzará mantenimiento/rollout sin una vía comprobada y autorización concreta.

Contrato y runbook en docs/architecture/memory/backup-contract.json y
docs/operations/COGNEE_BACKUP_RESTORE.md. Se prepara verificador read-only
root-only/tmpfs y pruebas artificiales de corrupción/ausencia; no representan
un colector ejecutado ni una restauración real. Snapshot, publicación atómica,
checksums reales, RPO/RTO y restore siguen NO MEDIDOS/NO EJECUTADOS.
API Ready, cero reinicios; PostgreSQL Ready (contador previo 1). Dataset
observado 36/36, 2.226 nodos y 6.040 aristas. Sin cambios live, recursos
Kubernetes temporales, Secrets, timers, prune/unlock, commit o push.
