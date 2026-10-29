# CHOMS Platforms — Operational Worklog

Append concise, evidence-based entries. Do not store command transcripts,
credentials, tokens, user data, Secret values, or backup contents. Historical
entries are immutable; append an explicit correction when needed.

## 2026-08-14 — Backup and recovery

- **Action:** Versioned Kubernetes/database backups, NAS synchronization, GFS
  retention, consistent Nextcloud snapshots, and controlled restore testing.
- **Result:** Recovery automation published; documented restore test completed
  without modifying production data.
- **Commit:** `b5b8792 feat(backup): version Kubernetes recovery automation`.
- **Evidence:** [`stacks/backup/README.md`](../../stacks/backup/README.md),
  checksums, structured dump validation, and isolated restore validation.
- **Derived pending:** add an encrypted copy outside the NAS failure domain.

## 2026-08-15 — MariaDB hardening

- **Action:** Pinned the running image digest, selected `Recreate`, and added
  startup, readiness, and liveness checks.
- **Result:** One Ready replica, persistent data and Nextcloud consumer
  validated, no declarative drift.
- **Commit:** `2948d31 fix(mariadb): harden rollout and health checks`.
- **Evidence:** Deployment, `healthcheck.sh`, database accessibility, and
  Nextcloud health.
- **Derived pending:** size resources and test further security context changes
  only with sufficient metrics and storage-permission evidence.

## 2026-08-16 — Nextcloud reconciliation and secure sharing

- **Action:** Reconciled the already-published Nextcloud and BusyBox digests,
  then implemented an idempotent policy for password-protected public links,
  forced seven-day expiration, and disabled public upload.
- **Result:** Nextcloud 31 healthy, no upgrade pending, policy converged, and
  public file delivery documented.
- **Commit:** `c16fd81 feat(nextcloud): enforce secure public sharing` for the
  policy and documentation. Digest reconciliation required no new commit.
- **Evidence:** [`NEXTCLOUD_SHARING.md`](../operations/NEXTCLOUD_SHARING.md),
  runtime status, policy values, rollout health, and drift zero.
- **Derived pending:** none for the approved sharing policy.

## 2026-08-16 — Nextcloud public-sharing E2E

- **Action:** Ran an isolated temporary-user, file, and public-share exercise
  against the enforced sharing policy.
- **Result:** The later audit durably confirms that temporary user, share, file,
  and Secret residue were removed. Git does not contain a detailed HTTP
  assertion transcript, so this entry does not independently attest every
  historical request result.
- **Commit:** none; runtime-only validation by design.
- **Evidence:** Audit preflight recorded zero E2E residue and current runtime
  retains the enforced policy. No credentials or share tokens were persisted.
- **Derived pending:** retain this as a repeatable release-validation pattern;
  do not use real user data.

## 2026-08-16 — Kubernetes workload audit

- **Action:** Inventoried direct, Helm, and K3s-managed workloads; compared Git,
  runtime declarations, effective imageIDs, probes, resources, security, and
  storage.
- **Result:** 35 workloads attributed, no orphan direct workload, prioritized
  remediation plan published with a repeatable read-only collector.
- **Commit:** `3d10730 docs(platform): audit Kubernetes workload hardening`.
- **Evidence:** [`KUBERNETES_WORKLOAD_AUDIT.md`](../operations/KUBERNETES_WORKLOAD_AUDIT.md)
  and its versioned audit script.
- **Derived pending:** execute the documented order one workload at a time.

## 2026-08-16 — Redis hardening

- **Action:** Reconciled the running digest, changed the single-replica PVC
  deployment to `Recreate`, added authenticated Redis health probes, and set
  resources using observed behavior.
- **Result:** Redis Ready with zero restarts, persistent storage mounted,
  consumers healthy, and drift zero.
- **Commit:** `fc3df18 fix(redis): harden rollout and health checks`.
- **Evidence:** authenticated `PING`, rollout, endpoints, PVC, consumer and
  cluster health.
- **Derived pending:** none for the completed block.

## 2026-08-16 — PostgreSQL reconciliation

- **Action:** Reconciled runtime `postgres:17` to the identical digest already
  published in Git after validating backup, persistence, probes, resources,
  and the CHOMS Controller consumer.
- **Result:** Recreate rollout passed; database, endpoint, consumer, MariaDB,
  Nextcloud, nodes, and probes remained healthy; drift zero.
- **Commit:** none; Git already contained the correct desired state and no empty
  commit was created.
- **Evidence:** effective imageID match, successful `pg_isready`, validated
  logical backup, four steady-state probe cycles, and public consumer health.
- **Derived pending:** further non-root enforcement requires entrypoint and NFS
  permission testing.

## 2026-08-16 — MetalLB controller reconciliation

- **Action:** Applied only the controller Deployment document from the vendored
  manifest, replacing the runtime tag with its already-running digest.
- **Result:** RollingUpdate passed; webhook, IP pool, three speakers, edge VIP,
  public route, nodes, and Pods remained healthy; controller drift zero.
- **Commit:** none; Git already contained the correct desired state.
- **Evidence:** server dry-run, controller-only diff, `/metrics` probe, webhook
  dry-run, five liveness cycles, and stable VIP. One startup resource-version
  conflict was retried successfully and did not recur.
- **Derived pending:** reconcile the MetalLB speaker separately.

## 2026-08-17 — Persistent operational memory

- **Action:** Added repository instructions, current state, active roadmap,
  append-only worklog, and evidence-backed ADRs.
- **Result:** New sessions can reconstruct current context without conversation
  history; sensitive topology and credentials are excluded.
- **Commit:** recorded by the commit containing this entry.
- **Evidence:** Git history, current documentation, direct manifests, workload
  audit, and read-only runtime checks.
- **Derived pending:** maintain these files in each future state-changing task.

## 2026-08-17 — MetalLB speaker reconciliation rolled back

- **Action:** Validated and applied only `metallb-system/DaemonSet/speaker`,
  replacing the runtime `v0.15.2` declaration with the identical effective
  digest already published in the vendored manifest.
- **Result:** RollingUpdate respected `maxUnavailable: 1`; availability reached
  no lower than 2/3 and three critical public routes remained HTTP 200. After
  rollout, all three speakers repeatedly failed memberlist joins and two also
  reported immutable-node conflicts for the existing `ServiceL2Status`.
  Revision 1 was restored. Final runtime is again `v0.15.2`, with 3/3 Ready,
  zero restarts, the same effective digest, healthy controller/Traefik/Gateway,
  three Ready nodes, and no failed Pods.
- **Commit:** no operational commit; Git already contained the digest. The
  documentation commit containing this entry records the blocked result.
- **Evidence:** controller-only state remained unchanged; speaker-only dry-run
  and diff were exact; node-by-node rollout and rollback completed; TCP/7946
  was locally reachable on the control-plane node but blocked or unreachable
  from it to both workers; errors continued after rollback; VIP and routes
  remained available throughout.
- **Derived pending:** obtain explicit authority for a focused node-network and
  firewall diagnosis covering TCP/UDP 7946, determine correct
  `ServiceL2Status` ownership behavior, and close the `/metrics` scraping gap
  before retrying speaker digest reconciliation.

## 2026-08-17 — Non-mutating Kubernetes security baseline

- **Action:** Audited versioned Kubernetes and backup sources, active
  operational memory, image and workload controls, storage/recovery, RBAC and
  Secret handling, observability configuration, and declared public routes.
  Performed anonymous safe HTTPS checks without authenticating or changing the
  platform.
- **Result:** No Critical finding established. Published an evidence-ranked
  baseline and one-logical-block backlog. High priorities are protection of the
  public Prometheus interface, tested minimization of privileged device
  workloads, and an independent encrypted backup copy. MetalLB speaker remains
  Blocked and its rollout was not retried.
- **Commit:** recorded by the documentation commit containing this entry.
- **Evidence:**
  [`KUBERNETES_SECURITY_BASELINE_2026-08-17.md`](../audits/KUBERNETES_SECURITY_BASELINE_2026-08-17.md)
  and [`HARDENING_BACKLOG.md`](../audits/HARDENING_BACKLOG.md). The audit
  environment lacked Kubernetes/Helm clients, so current runtime RBAC, events,
  restart counts, effective images, and monitoring targets remain explicitly
  marked Needs evidence.
- **Derived pending:** protect only the Prometheus HTTPRoute with existing
  ForwardAuth in the next authorized change; separately capture the pending
  read-only runtime evidence from an authorized workstation. Privileged
  MetalLB readings by an authorized platform operator remain deferred.

## 2026-08-17 — Prometheus route protected by Authelia

- **Action:** Added an `authelia-forwardauth` Middleware in `monitoring`, added
  the minimal Prometheus `one_factor` policy, and attached only that Middleware
  to `HTTPRoute/prometheus`. The Prometheus Helm release was not changed.
- **Result:** Anonymous HTTPS redirects once to Authelia and reaches its login
  page without a loop. Both route parents report `Accepted=True` and
  `ResolvedRefs=True`; Prometheus stayed Ready with 24 targets up and none down,
  Grafana health remained successful, and no new Traefik, Authelia, Prometheus,
  datasource, Pod, or event error was observed.
- **Commit:** recorded by the commit containing this entry.
- **Evidence:** server-side dry-runs and exact per-resource diffs; validated
  Authelia configuration; three post-change observation cycles; stable Service,
  EndpointSlice, RWO NFS PVC, effective images, public routes, three Ready
  nodes, and final drift zero.
- **Derived pending:** capture `IAM-001`, `IAM-002`, and `OBS-003` as one
  read-only evidence block. Authenticated Prometheus access was not exercised
  because no authorized test credential was used.

## 2026-08-17 — IAM and observability evidence block

- **Action:** Audited all managed workload identities, projected tokens,
  effective Role/ClusterRole bindings, high-risk `can-i` permissions,
  Prometheus selectors, monitor CRs, targets, Services, EndpointSlices, and
  MetalLB metrics reachability using read-only control-plane access.
- **Result:** No Critical finding. Portainer has unversioned `cluster-admin`;
  four chart workloads have reducible Secret-read scope; 14 direct workloads
  use default SAs with tokens and no demonstrated API need. Prometheus has 24
  targets up and none down, but annotated workloads without monitors are absent.
  Speaker absence is caused by missing discovery resources, with an additional
  1/3 TCP/7472 reachability constraint.
- **Commit:** recorded by the documentation commit containing this entry.
- **Evidence:**
  [`KUBERNETES_IAM_OBSERVABILITY_AUDIT_2026-08-17.md`](../audits/KUBERNETES_IAM_OBSERVABILITY_AUDIT_2026-08-17.md),
  repeated effective-RBAC checks, target aggregates, CRD/operator health, and
  redacted endpoint tests. No Secret value or metrics payload was retained.
- **Derived pending:** replace only Portainer's cluster-admin binding after its
  required workflows are captured. Keep MetalLB speaker Blocked; do not combine
  metrics discovery with memberlist diagnosis.

## 2026-08-17 — Portainer IAM-001 read-only diagnosis

- **Action:** Correlated Portainer Git/history, runtime ownership metadata,
  targeted effective permissions, safe use evidence, route exposure, Pod
  security, storage metadata, and official feature documentation. No login,
  Secret, PVC data, workload, route, or RBAC change was performed.
- **Result:** The unversioned binding grants every tested administrative
  capability. No retained evidence demonstrates use of writes, Secrets, exec,
  RBAC, impersonation, tokens, nodes, storage, CRDs, or webhooks; audit logs and
  attributable managed fields are unavailable, so historical use remains
  unknown. The route uses native Portainer authentication without Authelia.
  A Secret-free viewer is the provisional minimum profile.
- **Commit:** recorded by the documentation commit containing this entry.
- **Evidence:**
  [`PORTAINER_IAM_001_DIAGNOSIS_2026-08-17.md`](../audits/PORTAINER_IAM_001_DIAGNOSIS_2026-08-17.md),
  repeated `can-i` checks, structured runtime metadata, sanitized log counts,
  route conditions, endpoint health, and Git history.
- **Derived pending:** the Platform owner must state whether Portainer needs
  mutations and identify exact verbs, resource kinds, namespaces, logs, and
  exec requirements. Only then design and review staged dedicated RBAC; do not
  remove the current binding during that decision task.

## 2026-08-18 — Portainer IAM-001 viewer migration

- **Action:** Implemented the owner-selected Profile A with an explicit,
  versioned `portainer-viewer` ClusterRole and binding, validated it through an
  isolated temporary identity, then removed only the unversioned
  `ClusterRoleBinding/portainer` to `cluster-admin`.
- **Result:** Approved inventory, event, metrics, storage and Pod-log reads
  passed with the real ServiceAccount. Secrets, tokens, writes, interactive Pod
  access, RBAC/delegation, CRD and webhook mutation all returned `no`.
  Portainer, its storage, endpoint and route, Authelia, Traefik and cluster
  health stayed stable across three cycles with no sanitized RBAC errors.
- **Commit:** recorded by the commit containing this entry.
- **Evidence:** server-side dry-run, RBAC-only diff, isolated and real-identity
  matrices, actual non-sensitive reads, three Ready nodes, zero Pending/Failed
  Pods, and final declarative drift zero.
- **Derived pending:** authenticated visual Portainer review remains pending
  because no login or credentials were authorized. Next execute only
  `SUP-001`, the Scrutiny collector digest pinning block.

## 2026-08-18 — Scrutiny collector SUP-001 digest pinning

- **Action:** Replaced only the collector's `v0.8.2-collector` tag with the
  identical effective digest already running on both expected DaemonSet Pods.
- **Result:** RollingUpdate progressed 0/2, 1/2, then 2/2 updated while keeping
  both collectors Ready. Both retained zero restarts and two devices per
  anonymized node; startup collection completed on each, and the server
  accepted two registrations and four SMART uploads without failed posts.
- **Commit:** recorded by the commit containing this entry.
- **Evidence:** matching pre-change image IDs, image-only runtime diff,
  `maxUnavailable: 1`, three post-change cycles, API health 200, stable server
  storage metadata, healthy route and EndpointSlice, zero new warning events,
  three Ready nodes, zero Pending/Failed Pods, and final collector drift zero.
- **Derived pending:** `RES-002` remains next for separately designed probes
  and resources. `SEC-002` collector privilege/device minimization and
  `SEC-003` server hardening remain pending and unchanged.

## 2026-08-18 — Scrutiny collector RES-002 resource boundaries

- **Action:** Reviewed the v0.8.2 entrypoint, PID 1 process tree and one-shot
  collector behavior, then added only CPU and memory resources to the
  collector DaemonSet. Seven days of Prometheus data showed per-node peaks of
  5.19–6.24 mCPU, 8.31–10.18 MiB working set and 5.52–6.86 MiB RSS, with zero
  OOM events; observed startup collections completed in 0.91–1.91 seconds.
- **Probe decision:** Startup, readiness and liveness probes are not applicable
  currently. Cron is the persistent process, no Service consumes readiness,
  and v0.8.2 exposes no supported endpoint or durable health marker. PID checks
  duplicate runtime supervision, while disk, server or network checks would
  turn external/transient failures into restart loops.
- **Result:** Requests are `10m` CPU and `32Mi` memory; limits are `250m` CPU
  and `128Mi` memory. RollingUpdate retained `maxUnavailable: 1` and converged
  sequentially to 2/2 Ready with zero restarts, unchanged digest, two devices
  per anonymized collector, completed collection and recent server ingestion.
- **Rollback:** `kubectl rollout undo daemonset/scrutiny-collector -n monitoring
  --to-revision=2`, with a five-minute timeout.
- **Commit:** recorded by the commit containing this entry.
- **Derived pending:** execute only `SEC-002` next. Collector privilege/device
  minimization and `SEC-003` server hardening remain pending and unchanged.

## 2026-08-18 — Scrutiny collector SEC-002 privilege diagnosis

- **Action:** Ran server-dry-run-validated, non-uploading canaries one at a
  time on both collector nodes using the pinned image. The privileged baseline
  and all reduced variants performed only device discovery plus non-destructive
  `smartctl --info` and `--xall` reads; raw device output was discarded.
- **Evidence:** The privileged reference completed 2/2 reads on both nodes.
  The proposed non-privileged `SYS_RAWIO`/drop-all/no-escalation/
  `RuntimeDefault` profile discovered two devices but failed both opens on both
  nodes. The same failures remained with seccomp unconfined and with every
  capability, proving a containerd device-cgroup denial rather than a missing
  capability. Kubernetes rejected hostPath block devices in `volumeDevices`,
  which supports only PVC/Ephemeral block-mode sources. Read-only rootfs
  canaries failed before startup with three read-only-filesystem errors from
  the entrypoint/cron path.
- **Decision:** No production change. Controls declared alongside
  `privileged: true` would be ineffective: privilege escalation, all
  capabilities and unconfined seccomp/AppArmor are forced by Kubernetes.
  SEC-002 is blocked pending an approved device-plugin/CDI/DRA or equivalent
  mechanism that creates stable per-device cgroup rules.
- **Result:** All canaries were deleted; no temporary Pod, ServiceAccount, Role
  or binding remains. Production stayed 2/2 Ready with zero restarts, two
  recent devices per anonymized node, healthy ingestion and drift zero.
- **Rollback:** Not invoked because runtime was not changed. For a future
  failed attempt, restore the immediately prior DaemonSet revision within five
  minutes.
- **Commit:** recorded by the documentation commit containing this entry.
- **Derived pending:** Resolve the SEC-002 device-mapping prerequisite. Do not
  continue with `SEC-003` in this work block; it remains pending and untouched.

## 2026-08-19 — Scrutiny collector SEC-002 device-plugin review

- **Action:** Reviewed only the official [generic plugin repository](https://github.com/squat/generic-device-plugin)
  and [NVIDIA plugin repository](https://github.com/NVIDIA/k8s-device-plugin);
  no component,
  Kubernetes resource, manifest or runtime setting was changed.
- **Result:** The generic plugin is technically plausible through `DeviceSpec`,
  but its published DaemonSet is privileged and mounts the complete `/dev`,
  transferring rather than eliminating the risk. The NVIDIA plugin is for
  NVIDIA GPUs and does not apply to Scrutiny SATA/SAS devices. No candidate
  demonstrated the required security, maintenance and K3s/containerd
  compatibility, and developing one for four disks is not recommended.
- **Decision:** Preserve the current design and accept its residual risk
  temporarily. SEC-002 remains `blocked`, not completed. Restricted host
  service collectors are a possible future alternative requiring a separate
  architectural decision and work block.
- **Derived pending:** Do not execute `SEC-003`; it remains pending and
  untouched.

## 2026-08-19 — Scrutiny server backup prerequisite design

- **Action:** Performed a read-only diagnosis of the Scrutiny server's
  persistent paths, InfluxDB version, storage metadata and existing backup
  automation. No backup, snapshot, restore, restart, Kubernetes change or
  file modification was performed.
- **Result:** Scrutiny `0.8.2` embeds InfluxDB `2.2.0`; current backup coverage
  excludes its 28 KiB SQLite configuration and approximately 104 MiB InfluxDB
  data. Direct hot copying of the InfluxDB tree is unsafe. The image lacks the
  `influx` CLI, so a future implementation needs a compatible tool or
  authenticated API backup through a Secret reference without exposing values.
- **Design:** Use official InfluxDB backup/restore plus a consistent SQLite
  backup. Reserve 250 MiB per copy and 1 GiB for isolated restore staging;
  target RPO is 24 hours and RTO 1–2 hours. An isolated restoration is
  mandatory before SEC-003 changes.
- **Decision:** SEC-003 remains `pending`. SecurityContext, hostPath,
  devices and the Scrutiny server remain unchanged.

## 2026-08-19 — Filebrowser IMG-003 digest pinning

- **Action:** Replaced only `filebrowser/filebrowser:s6` in the Filebrowser
  Deployment with the exact already-running digest
  `docker.io/filebrowser/filebrowser@sha256:ee4ac79e52966a5f6247f99c7d667c1debfb277a3a61ab829f505aa8f4c74b21`.
- **Result:** Server-side dry-run and controller-only diff passed. The single
  Recreate rollout completed successfully; the Pod remained Ready with zero
  restarts and its declared image matched the effective imageID exactly.
  Service, EndpointSlice, HTTPRoute, Authelia, local HTTP response, storage
  mounts/files, three Ready nodes and zero Pending/Failed Pods remained healthy;
  no warnings were present and the final full-manifest diff was empty.
- **Scope:** No probes, resources, securityContext, ServiceAccount, ports,
  mounts, storage, route, network, configuration or other workload changed.
- **Derived pending:** SEC-003 remains pending and untouched; no subsequent
  workload was started.

## 2026-08-19 — Home IMG-001 digest pinning

- **Action:** Replaced only `nginx:stable-alpine` in the Home Deployment with
  the exact already-running digest
  `docker.io/library/nginx@sha256:97d490c12ba55b4946b01546d1c3ed324e8d41ab1c9fcb2a616aa470620e5b46`.
- **Result:** YAML, server-side dry-run and controller-only diff passed. The
  two-replica RollingUpdate completed; both Pods remained Ready with zero
  restarts and imageIDs matching the declared digest. Service, EndpointSlice,
  HTTPRoute/auth response, ConfigMap metadata, mounted files, three Ready
  nodes, zero Pending/Failed Pods and zero warnings remained healthy.
  Controller drift is zero; unrelated pre-existing full-manifest ConfigMap
  content drift was preserved and not changed.
- **Scope:** No probes, resources, securityContext, ServiceAccount, ports,
  mounts, content, Service, route, TLS, Authelia, network or other workload
  changed.
- **Derived pending:** SEC-003 remains pending and untouched; Authelia and
  all other workloads were not started.

## 2026-08-21 — Scrutiny cold-bootstrap recovery prerequisite

- **Action:** Added manual, non-recurring cold-backup and isolated-restore
  procedures. A mount preflight passed before scaling only the Scrutiny server
  to zero. Configuration and InfluxDB state were copied from read-only hostPath
  mounts to a restricted NAS staging directory, checksummed and published by
  atomic rename. Production interruption was 83 seconds.
- **Restore evidence:** A separate 1 GiB `emptyDir` restore passed SQLite
  `integrity_check` plus InfluxDB 2.2.0 series, TSM, WAL and tombstone checks.
  The pinned Scrutiny 0.8.2 image and embedded InfluxDB then started healthy
  without Service, route, host port or collector endpoint. Two earlier
  temporary Pods failed before validation because of copy path/ownership
  handling; both were removed before the corrected run passed.
- **Result:** Scrutiny returned 1/1, collectors remained 2/2, recent ingestion
  and the API were healthy, all three nodes were Ready, no Pods were
  Pending/Failed, no Warning appeared after stabilization, and server plus
  collector drift was zero. Temporary Pods, Jobs, locks, partial copies and
  restored data were removed. Production data and manifest fields were not
  changed.
- **Security:** The backup is mode `0700` because InfluxDB 2.2 metadata
  contains authentication material. No token or database content was read or
  logged, and no Secret, recovery command, recurring schedule or automated
  backup was introduced.
- **Derived pending:** `SEC-003` remains pending. Controlled operator-token
  recovery and the official recurring backup needed for RPO 24h require
  separate authorization and validation.

## 2026-08-21 — Scrutiny dedicated InfluxDB backup authorization

- **Action:** Used the official offline InfluxDB 2.2.0
  `influxd recovery auth create-operator` command while only
  `Deployment/monitoring/scrutiny` was at zero. A temporary Pod used the exact
  pinned Scrutiny image, mounted only the InfluxDB host path, had no
  ServiceAccount token, and retained no command output in its logs.
- **Secret handling:** The v2.2.0 command prints all authorizations, so stdout
  and stderr were consumed by a strict closed pipeline. Exactly the new token
  and authorization ID were sent by stdin to the atomic creation of
  `monitoring/scrutiny-backup-influx-operator`; neither value, token fragment,
  reversible hash nor response body was displayed or persisted elsewhere.
  Git records only the object and key contract.
- **Validation:** The Secret contains exactly `token` and `authorization-id`,
  both non-empty. Authentication against that authorization returned HTTP 200
  with the body discarded. The first client-side validation attempt had an
  invalid local `jq` quoting expression; production had already returned 1/1,
  and the corrected stdin-only check passed without another recovery command
  or interruption.
- **Result:** The recorded scale interval was 43 seconds. Scrutiny is 1/1,
  collectors are 2/2 with recent successful collection, three nodes are
  Ready, no Pod is Pending/Failed, no new Warning or temporary resource
  remains, storage mounts are intact, and server plus collector drift is zero.
- **Scope:** No recurring backup, restore automation, CronJob, production
  image, security context, device, host path, application configuration or
  other workload changed. `SEC-003` remains pending until the official
  recurring RPO-24-hour backup and isolated restore pass.

## 2026-08-22 — Scrutiny recurring logical backup prerequisite

- **Action:** Added an internal InfluxDB backup Service, script ConfigMap and
  daily `scrutiny-logical-backup` CronJob. Official `influx backup` receives
  the dedicated Operator token only through `secretKeyRef`; Python's
  `sqlite3_backup` API creates a transactional SQLite copy from a read-only
  production mount. Publication uses a mode-0700 staging directory, lock,
  file-size and SHA-256 manifests, atomic rename and 7/8/12/5 GFS retention.
- **Security:** Both pinned tool images run without privilege, host namespaces,
  ServiceAccount tokens, added capabilities or privilege escalation, with
  `RuntimeDefault` seccomp and read-only roots. UID/GID 0 is retained only
  because a non-root preflight could not traverse the existing mode-0700 NAS
  and source host paths. The token was neither displayed nor persisted outside
  its existing Secret.
- **Backup evidence:** Two preliminary manual Jobs failed before publication:
  the first image had no Bash and the second exposed a BusyBox/GNU `find`
  incompatibility. Both left zero partial copy or lock and were deleted. The
  corrected POSIX Job succeeded and published one 17-file logical copy with
  valid checksums. No GFS promotion was due; the cold bootstrap checksum set
  remained valid.
- **Restore evidence:** SQLite copy and `integrity_check`, full `influx
  restore`, offline TSM/series and applicable WAL validation, and isolated
  Scrutiny 0.8.2/InfluxDB 2.2.0 startup passed in a 1 GiB `emptyDir`. Earlier
  isolated attempts identified writable InfluxDB metadata-path requirements
  and an invalid post-full-restore token assumption; they changed no
  production state and were removed before the final successful run.
- **Result:** The daily 02:45 Europe/Madrid schedule is active with
  `concurrencyPolicy: Forbid`, a 20-minute deadline and 1/1 successful/failed
  history limits. Scrutiny remained 1/1, collectors 2/2 with healthy recent
  ingestion, all three nodes Ready and no unhealthy Pod. Six Warning events
  from the removed preliminary Jobs/Pods remain in event history; none occurred
  after the final successful stabilization. No temporary Job, Pod, lock or
  partial copy remains.
- **Scope:** Production Scrutiny, privileges, security context, image,
  configuration, devices, host paths and collectors were not modified.
  `SEC-003` remains pending; only its backup prerequisite is complete.

## 2026-08-22 — NAS Scrutiny collector digest pinning

- **Action:** Replaced only the NAS collector's mutable
  `v0.8.2-collector` image reference with the exact digest already present and
  running. Because the historical container was not Compose-managed, it was
  recreated through the local Docker API from its effective configuration;
  the prior container remained stopped as rollback until validation passed.
- **Validation:** Non-image runtime comparison passed with zero drift. The new
  container stayed running with zero restarts and completed one startup cycle
  covering five devices, five SMART reads and five publications, with no
  permission, access or publication error. The central API confirmed the same
  five-device origin and 11 unique recent devices overall, proving zero
  overlap with the six active Kubernetes devices.
- **Result:** The stopped rollback container was removed only after central
  validation; the prior image remains locally available. Three Kubernetes
  nodes remained Ready, Scrutiny stayed 1/1, collectors stayed 2/2, and no Pod
  became Pending or Failed.
- **Scope:** Privilege, capabilities, mounts, environment, host identity,
  endpoint, six-hour schedule, startup behavior, network and filesystems were
  unchanged. No smartmontools installation, native migration, mdraid work,
  Kubernetes change, `SEC-002` or `SEC-003` work was performed.

## 2026-08-22 — NAS mdraid monitoring diagnosis

- **Action:** Revalidated the digest-pinned NAS Scrutiny collector and performed
  a read-only diagnosis of `mdmonitor.service` and
  `mdmonitor-oneshot.service`. No collector reconciliation was needed because
  the declared and effective image digests already matched.
- **Evidence:** The kernel reports one active mdraid array, with no degraded
  member or resynchronization. Both static, triggered monitoring units exit
  with status 1 and leave no monitor process active. Unit flags, the mdadm
  configuration entry and the default daemon setting are present, but the
  unprivileged account cannot read the unit journal; a narrowly scoped
  non-interactive sudo journal query was denied.
- **Decision:** The cause is not yet unequivocal. Because an active array
  exists, neither unit was disabled, masked, restarted or modified. No RAID,
  disk, partition, filesystem or package operation was attempted. Resolution
  remains blocked pending privileged read-only journal evidence and a separate
  authorization for any proven reversible configuration-only correction.
- **Validation:** NAS filesystems and NFS remained accessible, the GFS timer
  and latest backup service result were healthy, and the collector remained
  running with zero restarts after a complete five-device publication cycle.
  Central Scrutiny reported 11 unique recent devices with zero duplicates;
  Scrutiny was 1/1, collectors 2/2, all three nodes Ready, and no Pod was
  Pending or Failed. NAS and Kubernetes received no mutation in this block.

## 2026-08-22 — NAS mdraid local monitoring correction

- **Cause:** mdadm refused to monitor because neither `MAILADDR` nor `PROGRAM`
  was configured; an earlier event had also attempted to use an absent local
  mail transport. SMTP, credentials and packages were deliberately excluded.
- **Change:** Added versioned systemd drop-ins that leave the vendor units in
  place and append `--syslog` to their mdadm monitor commands. The permanent
  service runs continuously. The oneshot resets and restores the vendor
  environment-file declaration and retains conditional execution under
  `AUTOSCAN=true`.
- **Correction during validation:** The initially applied oneshot drop-in ran
  mdadm directly and bypassed `AUTOSCAN`. Before commit it was reconciled to
  the conditional vendor semantics using an exact-state guard and automatic
  rollback. The source, installed override and effective unit now agree.
- **Validation:** The permanent monitor is active/running; the conditional
  oneshot completed with result `success` and exit status 0. Both effective
  commands use `--syslog`, no related unit is failed, and the monitor process
  is present. One array remains active and complete with no rebuild or
  resynchronization. No synthetic RAID event was generated; syslog/journal is
  the configured local delivery path, while external Alertmanager delivery
  remains pending.
- **Consumers:** Storage and NFS remained accessible, the GFS timer and latest
  backup result stayed successful, and the digest-pinned NAS collector stayed
  running with zero restarts. Kubernetes remained 3/3 Ready with Scrutiny 1/1,
  collectors 2/2 and no Pending/Failed Pod. All staging and reconciliation
  temporaries were removed. No array, disk, filesystem, mount, package,
  Scrutiny, Docker, NFS, backup or Kubernetes configuration changed.

## 2026-08-22 — Scrutiny SEC-003 Hub/Spoke migration

- **Baseline:** 12 stored records reconcile to 11 active unique devices
  (`2+2+2+5`) plus one inactive July record; no overlap or deletion.
- **SQLite:** UID/GID is 0 for both images. `1000:1000 0755` failed API writes
  after dropping capabilities and `fsGroup` did not help. Minimal `0:0 0755`
  passed synthetic registration, restart persistence and integrity checks.
- **Change:** Split pinned web/API 0.8.2 and InfluxDB 2.2.0; removed web
  privilege, devices, udev, hostPort, Influx mount and ServiceAccount token;
  switched collectors to Service DNS and added S as the third collector.
- **Validation:** S published two devices without HTTP 500. A post-change
  backup and full isolated Hub/Spoke restore with API write/restart passed.
- **Rollback:** Stop split workloads, remove S label, restore omnibus and
  config ownership `1000:1000`; restore data only on proven corruption.

## 2026-08-23 — Colegio staging Checkpoint 1

- **Scope:** Applied only the three educational Certificate SANs, three CoreDNS
  split-DNS records, three Authelia one-factor rules and the institutional web
  resources. Moodle and Gibbon remain separate checkpoints.
- **Validation:** Certificate generation 10 is Ready; CoreDNS and Authelia are
  1/1; the web Deployment is Ready with an EndpointSlice; six pages load,
  `private-assets-review` is excluded, the HTTPRoute is Accepted with resolved
  references, and anonymous HTTPS redirects through ForwardAuth.
- **Security:** Web runs from the verified immutable public digest without a
  ServiceAccount token, privilege escalation, capabilities, host access or a
  writable root filesystem. No Secret values or private key material entered
  Git. The shared staging cookie remains an explicitly authorized residual
  risk.
- **Rollback boundary:** Later Moodle or Gibbon failures roll back only their
  own resources; this foundation remains intact.

## 2026-08-23 — Colegio staging Checkpoint 2

- **Scope:** Completed Moodle 5.2.2/MariaDB 11.4 staging only. The declarative
  activity validation uses the complete official assign defaults, including
  `visible=1`, the four authorized grading defaults and nullable multimarking
  fields. No Gibbon resources were deployed.
- **Validation:** Fictional course and task persist in the active PVCs; the
  real CronJob completed successful cycles. The Moodle ClusterIP Service and
  `colegio-aula.chomsmaster.com` HTTPRoute are healthy on `web` and `websecure`
  with the existing Authelia ForwardAuth.
- **Recovery:** Logical MariaDB, configuration and `moodledata` backup was
  checksum-verified. An isolated restore preserved the schema, fictional
  course/task and `moodledata/filedir`. The restore marker is explicitly
  artificial/operational and contains no user data. Temporary restore
  resources and backup artifacts were removed.
- **Security:** No Secret values, dumps, private keys, personal data or logs
  entered Git. Checkpoint 1 remains an independent rollback boundary.

## 2026-08-23 — Colegio staging Checkpoint 3 declarativo

- **Scope:** Deployed only Gibbon 30.0.01 staging resources: independent
  MariaDB, database/runtime PVCs, runtime Secret, pinned bootstrap Deployment,
  ClusterIP Services and the `colegio-gestion.chomsmaster.com` HTTPRoute.
- **Protection:** The route is attached to `web` and `websecure` and uses the
  existing Authelia ForwardAuth. The official installer bundle is present and
  reachable behind authentication.
- **Boundary:** The manual web installer was not completed, no account or real
  data was created, and no Gibbon import or migration occurred. The runtime
  PVC is intentionally mutable because this is an official installer
  requirement. Checkpoints 1 and 2 remain independent and untouched.
- **Security:** The image is pinned by digest; the Pod has no privileged mode,
  hostPath, hostPort or ServiceAccount token. Secret values and credentials are
  runtime-only and absent from Git.

## 2026-08-25 — Traefik Gateway Shim warning correction

- **Cause:** The obsolete Gateway issuer annotation made cert-manager Gateway
  Shim inspect intentionally hostname-less listeners, while TLS was already
  owned by the separate `traefik/choms-platform` Certificate. The versioned
  Helm values also omitted several user-supplied settings from the live
  release, so an initial render correctly blocked application due to unrelated
  drift.
- **Change:** Recovered only the explicit live Gateway, provider, replica,
  affinity, resource and Service contract into the existing Traefik values,
  then removed `cert-manager.io/cluster-issuer`. Chart 41.1.0, Traefik v3.7.9,
  listeners, redirect, LoadBalancer VIP, RBAC, ports and TLS Secret reference
  were preserved.
- **Validation:** Full Helm template, server dry-run and manifest comparison
  reduced the effective diff to the single annotation removal before one
  atomic release upgrade. Traefik remained 2/2; Gateway stayed Accepted and
  Programmed; `choms-platform` stayed Ready at revision 6 and continued to
  reference `choms-platform-tls`. Public HTTPS returned 200, the protected
  dashboard redirected to Authelia, and the warning count remained zero after
  reconciliation. No certificate issuance, renewal or ACME test occurred.

## 2026-08-27 — Alertmanager Telegram critical delivery

- **Change:** Configured the locked monitoring release to select and mount the
  external `monitoring/choms-monitoring-alertmanager-config` Secret. Added a
  reusable interactive SSH-based script that creates or rotates the Secret by
  server-side apply over stdin without placing its bot token or chat identifier
  in Git, arguments, logs or remote files.
- **Routing:** `critical` alerts use Telegram with resolved notifications;
  `Watchdog`, `warning` and unmatched alerts remain on `null`. The three
  historical `KubeJobFailed` alerts therefore remain visible without sending
  notifications.
- **Validation:** A real `CHOMSTelegramIntegrationTest` firing and resolved
  notification reached Telegram. An initial `chat not found` failure was
  diagnosed and corrected by reconciling the verified bot/chat pair without
  exposing credentials. The resulting delivery-failure alert then resolved
  naturally, with no silence, rule change or deletion. Prometheus and
  Alertmanager remained 1/1 and no new Telegram failure followed reconciliation.
- **Reuse:** The RP3 may later reuse the same bot/chat destination, but must
  keep and rotate its own credential material independently of Kubernetes.

## 2026-08-27 — Raspberry Pi external monitor phase 1

- **Change:** Deployed one approximately 15.6 MiB ARMv7 monitor container on
  the US RP3. It checks representative external DNS, HTTPS, TLS expiry,
  expected response and latency plus restricted local capacity, mount,
  temperature, throttling and exact-name Firefox-running signals. A hardened
  user service supplies host facts without mounting `docker.sock`; the
  container is non-privileged, read-only, capability-free and PID/CPU bounded.
- **Alerting and secrets:** Persistent state sends one FIRING after three
  consecutive failures, no periodic repeats, and one RESOLVED after recovery.
  Controlled FIRING and RESOLVED notifications were received. Telegram token
  and chat ID are independent mode-0600 files on the RP3, ignored by Git and
  installed or rotated through a no-echo interactive script.
- **Corrections:** Stable anonymous GETs established Nextcloud `302` to its
  login and protected Home `302` to the declared `auth.chomsmaster.com`. The
  HTTP client now explicitly avoids redirects. The initial read-only report
  observed the helper's `ProtectSystem=strict` namespace, so it now reads the
  PID 1 mount namespace and correctly reports the host root as read-write. Both
  HTTP incidents and the read-only component emitted RESOLVED and are inactive.
- **Residual incident:** `rp3-local` remains firing exclusively for
  `throttled=0x50005`, meaning undervoltage and throttling are current and have
  also occurred since boot. Temperature was 63.4–65.0 C with no thermal
  throttle bits. Fit a known-good regulated 5.1 V / 2.5 A supply and a short,
  low-resistance micro-USB cable; do not reboot before correcting power.
  Current bits must clear with stable power and the alert should resolve
  automatically. Historical bits require a later controlled reboot.
- **Validation and limitation:** Final state was healthy with zero restarts;
  public and protected checks had zero failures, host root was not read-only,
  and only the electrical incident remained active. This RP3 kernel cannot
  enforce the declared container memory limit; the limitation is accepted
  without changing kernel or Docker configuration. WireGuard, SSH/SOCKS,
  Firefox, Docker global state and other services were not modified.

## 2026-08-29 — NAS Scrutiny collector endpoint recovery

- **Cause:** The manually created NAS collector retained the retired
  `192.168.1.138:8083` endpoint after the Scrutiny Hub/Spoke migration and its
  six-hour publications timed out. The current ClusterIP is not routed to the
  NAS, while the existing HTTPS route to `monitoring/scrutiny:8080` is
  reachable and healthy.
- **Change:** Added a minimal Compose declaration and reusable SSH deployment
  workflow. Recreated only `choms-scrutiny-collector` with the HTTPS endpoint;
  image digest, host identity, startup collection, six-hour cron, privilege,
  `/dev`, read-only udev, bridge networking and restart policy were preserved.
- **Validation:** The guarded preflight proved the endpoint was the sole
  effective delta. One normal startup collection read and published five
  devices with no send error. The same five hashed identities refreshed, the
  complete identity set remained unchanged, no duplicate appeared, Scrutiny
  stayed healthy, and the collector runs with zero restarts. RAID remained
  `[UUUU]` and NFS active. No SMART self-test, disk, RAID, filesystem, NFS,
  Kubernetes, image, credential or unrelated-container change occurred.

## 2026-08-29 — Actionable NAS, node and storage monitoring

- **Change:** Added one private NAS node-exporter using the same pinned digest
  as Kubernetes. It is non-privileged, read-only, capability-free and limited
  to filesystem, diskstats, hwmon, mdadm and textfile collectors. An
  unprivileged persistent user timer publishes atomic, unlabeled NFS,
  mdmonitor, RAID and Scrutiny freshness summaries every minute. No raw device,
  Docker socket, systemd collector, credential or SMART command is present.
- **Prometheus:** The locked kube-prometheus-stack 88.0.1 release now scrapes
  `instance=choms-nas, role=nas`. Thirteen CHOMS rules page only persistent
  actionable NAS, node and PVC conditions; upstream critical filesystem/PVC
  capacity rules are reused instead of duplicated. Routing and upstream
  severities were unchanged.
- **Corrections:** The first user timer used `OnUnitActiveSec`, which left no
  next elapse for the completed oneshot and correctly triggered the stale
  alert. It was reconciled to a per-minute calendar timer. `AF_UNIX` was added
  to the hardened service so unprivileged systemd state queries work. Docker
  bridge publication restricted to the NAS LAN address made the target
  reachable without a firewall or privileged change. An ambiguous Scrutiny
  device status was deliberately not converted into SMART failure telemetry.
- **Validation:** YAML, Bash, Python, systemd units, Compose render, promtool
  syntax and unit tests passed. Helm server dry-run passed and the persistent
  diff contained only Prometheus, its generated scrape Secret and the new
  PrometheusRule. A synthetic metric produced Telegram FIRING and RESOLVED as
  confirmed by the operator, then was removed. Final evidence showed
  `Linger=yes`, timer enabled/active, a 10-second-old textfile, exporter running
  unprivileged with zero restarts, NAS target UP and no CHOMS alert. RAID,
  NFS, Scrutiny, Prometheus and Alertmanager remained healthy. No RP3, disk,
  RAID, filesystem, NFS, PVC, chart version or unrelated service changed.

## 2026-08-30 — Isolated Kubernetes database recovery validation

- **Scope:** Used only package `20260830-031918` and the exact production
  MariaDB, PostgreSQL and Redis image digests. Each run created a uniquely
  labelled temporary namespace with default-deny ingress/egress, three
  independent local-path PVCs and one ephemeral random-credential Secret. No
  Service, route, public DNS, production PVC or production Secret was used.
- **Corrections:** The first attempt timed out before restore because the
  control-plane toleration was missing. The second restored successfully but
  exposed weak acceptance logic: MariaDB's `--databases` dump restored its own
  database name while the query checked another, and Redis parsing expected a
  labelled result. Both attempts ran guarded cleanup with no residual PV. The
  final script requires non-zero MariaDB database/table counts and a numeric
  Redis key count before reporting success.
- **Result:** Checksums passed. MariaDB restored 1 database and 127 tables from
  a 1,886,603-byte artifact in 24.880 seconds. PostgreSQL restored 1 non-system
  schema and 1 table from 4,736 bytes in 2.573 seconds. Redis loaded 6 keys
  from 53,267 bytes in 1.061 seconds. All engines passed synthetic
  write/read/delete checks without printing restored values or rows. Eight
  non-sensitive configuration files were extracted into a temporary directory,
  structurally checked and removed without application.
- **Isolation and cleanup:** All three Pods became Ready, restore commands
  returned without error, endpoint count remained zero, production database
  Deployments plus Prometheus/Alertmanager resource versions were unchanged,
  and the active critical-alert count had zero delta. Exact-name and label
  guards then inventoried and deleted only the final namespace. Namespace,
  temporary PVCs/PVs/Secret, outside resources and Released-PV residue were
  absent; the backup package was preserved.
- **Residual risk:** There is still no encrypted independent/off-site copy,
  external Secrets are not proven recoverable, and multiple application PVCs
  and node-local state paths remain without backup coverage.

## 2026-08-30 — Encrypted recovery copy declarative preparation

- **Scope:** Prepared a restic 0.18.0 design for the authorized existing ext4
  destination on node-03. It declares a chrooted, key-only SFTP account,
  independent source-restricted Ed25519 keys, direct per-node password entry,
  local/SFTP backends, stable host/type tags, serialized timers, retention
  dry-run only, source-side encryption, textfile metrics and critical alerts.
- **Recovery content:** The scope covers the validated Kubernetes database
  package, selected small configuration/state, encrypted Kubernetes Secrets,
  and a transactional SQLite copy of the documented K3s datastore. It rejects
  etcd, external datastore and cluster-init indicators rather than copying
  `server/db` hot. Bulk Nextcloud data, media, downloads, Colegio, personal
  backups, Prometheus, Loki, caches and unrelated NAS storage are excluded.
- **Safety boundary:** No remote command or runtime mutation was performed.
  No user, chroot, SSH key, known-host entry, repository, password, installed
  unit, timer or backup was created. Real forget and prune remain disabled;
  deployment and restore validation require a separate authorized block.

## 2026-08-31 — Encrypted node-03 recovery checkpoint completed

- **Deployment:** Initialized one encrypted Restic repository on the existing
  node-03 ext4 HDD. Node-01 and node-02 use independent source-restricted SFTP
  identities into a root-controlled chroot that exposes only the repository;
  node-03 accesses the same destination locally. Password material and private
  keys remain outside Git, and recovery-password custody was confirmed
  externally.
- **Scope:** Six hostname/type categories cover the validated database package,
  authorized small platform/Kubernetes state, encrypted Secret exports,
  consistent SQLite K3s state, selected Nextcloud configuration/application
  state, Jellyfin configuration configuration. Nextcloud data,
  multimedia, downloads, Colegio, personal/historical backups, Prometheus TSDB,
  Loki, caches and unrelated storage remain excluded.
- **Validation:** `restic check`, hostname/tag and exclusion validation passed.
  Aggregate size is 1,242,635,604 logical bytes and 1,108,695,459 stored bytes,
  below the 25 GiB limit. Backup timers at 05:00, 05:30 and 06:00 plus the 06:30
  maintenance timer are enabled, active and waiting in Europe/Madrid. Retention
  is 7 daily, 4 weekly and 6 monthly; maintenance remains `forget --dry-run`
  only, with no real forget, prune or automatic unlock.
- **Monitoring and closure:** The authorized monitoring release change mounted
  each node's textfile directory read-only, loaded two Restic rules and retained
  Grafana PVC identity and binding. Node-exporter remained 3/3, Prometheus and
  Alertmanager 1/1, all three node metric sets were ingested, and no unexpected
  Restic alert was active. The operator confirmed the single controlled FIRING
  and RESOLVED in Telegram; its temporary signal was removed and Prometheus
  ended inactive.
- **Recovery boundary:** This copy is independent of the NAS but still local,
  not offsite. Recovery requires the node-03 HDD, the externally held password
  and a compatible Restic version. Loss of the site or that HDD remains an open
  risk addressed by the separate off-site roadmap item.

## 2026-09-23 — Restic node-01 freshness correction closure

- **Scope:** Closed validation of the already deployed correction only. Removed
  the fixed 30 August package reference, selected the newest validated package
  with no stale fallback and maximum RPO 24 hours, and measured actual node-01
  logical scope. Execution success and protected-data freshness are separate.
- **Controlled execution supplied by operator:** 20:49:42–20:49:59 CEST,
  Result=success, duration 17 seconds, 167,611,546 bytes, package age 63,113
  seconds and package_valid=1. Execution timestamp 1790189382, last success
  1790189399, candidate/protected package timestamp 1790126274.
- **Read-only runtime evidence:** Both installed SHA-256 hashes matched the
  prepared scripts. The exact node-01 timer was enabled/active/waiting;
  service inactive/dead with Result=success. Prometheus matched all nine
  metric values and had zero Restic firing alerts. An initial query used the
  generic timer name; the corrected exact node-01 unit confirmed its state.
- **Local validation:** Bash syntax passed for three shell files; the synthetic
  test ran once with 56 checks passed. Diff whitespace and limited sensitive
  review passed. ShellCheck was unavailable; nothing was installed/downloaded.
- **Boundaries:** No backup, Restic command, restore, sudo, service/timer start,
  routing change or node-02/node-03 mutation. Root-only rollback retained.
  Node-02/node-03 constant sizes and the historical scope validator remain
  separate debt. The recovery copy remains local, not offsite.
- **Git handoff:** Operator reported fetch outside the sandbox; local references
  confirmed HEAD == origin/main with divergence 0/0. No additional fetch,
  commit or push was attempted. The reviewed diff is prepared for one manual
  commit, `fix(backup): enforce fresh database recovery package`, and push.


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

## 2026-10-24 — Exportador offline genérico

Sustituido el cifrado anterior por age con recipient público, allowlist explícita,
streaming, comprobación de estabilidad, manifiesto sanitizado, checksums y
publicación atómica. Harness aislado con fixtures sintéticos y claves efímeras;
sin kit, captura ni restauración reales. Cierre: 22 tests sintéticos PASS en
una ejecución, incluidos INT/TERM/HUP y descifrado sintético byte a byte.
Bash, ShellCheck de los dos wrappers, sintaxis Python, diff y revisión sensible
acotada PASS. SC2317 se anota solo en callbacks asíncronos probados. Kit real,
restauración y alineación de reglas del destino permanecen pendientes.

## 2026-10-24 — Recipient y presentación pública

Recipient público autorizado documentado; configuración auxiliar SOPS en el
repositorio de custodia y cifrado ficticio por stdin, sin plaintext persistente,
PASS. Se conservó el formato age de kits y no se ejecutó exportación real.
Notas de trabajo retiradas de la raíz y referencias ajustadas. README
sin IPs internas ni endpoints administrativos; roadmap fechado sin nuevas
afirmaciones runtime. About solo propuesto. Validación única y acotada de
sintaxis, links, exposición, contrato y revisión sensible; sin despliegues.

## 2026-10-24 — Referencias documentales retiradas

Eliminadas rutas obsoletas del handoff y salidas retiradas de los generadores;
contexto público simplificado, sin ejecutar scripts ni consultar producción.

## 2026-10-25 — Preparación de OmniRoute, preflight detenido

Checkout público main limpio y sincronizado al inicio; release oficial v3.8.52
verificada. Imagen publicada como 3.8.52 sin prefijo v; digest real fijado junto
a Redis 8.6.5-alpine. Preparados namespace, clase local Retain dedicada por
SQLite WAL, PVC, Deployments Recreate, ClusterIP, rutas y default-deny. Regla
Authelia exacta con default deny y ampliación SAN preparadas, no aplicadas.
Acceso kubectl por SSH sin sudo disponible. No colisiones namespace/hostname;
preflight posterior detenido porque una ruta protegida existente no cumplió
la redirección esperada. Causa HTTP exacta no registrada; no se repitió live.
No se llegó a dry-run servidor, generación de Secrets, aplicaciones ni rollout.
Sin solicitudes a modelos, backups/timers ejecutados o cambios en otros repos.
Validación final exclusivamente local; sin commit/push por falta de aceptación
runtime. Backup independiente, monitor Kuma y recuperación siguen pendientes.


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

### 2026-10-25 — Cognee: API/ingesta/persistencia aceptadas con RAM 8/16 GiB

Operador amplió node-02; Kubernetes confirmó Ready, MemoryPressure=False y
32759140 KiB allocatable. Cambio declarativo exclusivo de RAM 8/16 GiB;
CPU/modelos/imagen/políticas sin cambios. Dry-run y diff servidor acotados
pasaron; tras requests quedaron 19,54 GiB allocatable sin reservar.

Las APIs soportadas identificaron por hashes los 36 documentos parciales
(1 completo). Al no estar garantizado replay atómico tras OOM, se eliminó
solo ese dataset mediante DELETE soportado (200), sin SQL ni limpieza de PVC;
listado y accesos por API confirmaron su ausencia antes de add.

Único intento cognify: 36/36 completos; exit 0, duración 1895,629 s y CPU
3522,180 s. 191 muestras: pico cgroup 13102444544 bytes (12,20 GiB), máximo
working set muestreado 12769841152 bytes (11,89 GiB); RSS máximo del proceso
9612352 KiB. Cero eventos OOM/OOMKilled, cero reinicios y cero intentos HTTP
no autorizados registrados. No se activó ningún corte ni rollback.
CHUNKS recuperó fuentes del incidente OmniRoute y su runbook, SERVFAIL,
solver-nameservers, corrección de origen Flannel y commit c1af248.

Un único restart API preservó IDs de 36 documentos, índice 36/36 y grafo real
2.226 nodos / 6.040 aristas. Un sondeo SDK auxiliar falló por bloqueo de grafo
entre procesos: evidencia conservada, sin corrupción reportada ni rollback.
Se corrigió solo la vía del verificador a POST /api/v1/search, CHUNKS y
only_context=true: HTTP 200, hechos y fuentes correctos; lectura real del grafo
por API también 200. No se repitieron cognify, ingesta, modelos ni rollout.

MCP se evaluó estáticamente en la fuente oficial fijada: FastMCP se construye
sin contrato explícito de auth entrante; Host/Origin y CORS no la acreditan.
El token API es de salida; uv.lock resuelve cognee 1.6.3, no demuestra
compatibilidad con API 1.6.5. Candidato no admitido; handshake/tools/list no
se declaran pasados y no se crearon recursos MCP. API sana conservada.
Backup/restore diferido a bloque separado, sin prueba destructiva nueva.

Estado final: API 1/1 y PostgreSQL Ready; PVC/PV, Secrets, imagen y modelos
preservados. Solo ClusterIP, sin HTTPRoute/Ingress/ReferenceGrant ni IP externa.
Sin proveedores, inferencia generativa, otros servicios, commit o push.
Corpus: snapshot público admitido con hashes y base Git c1af248; los documentos
de cierre posteriores no se reingirieron. No implica que cambios sin commit
pertenezcan al árbol de ese commit. Evidencia en memory-gate.json.

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

### 2026-10-26 — Cierre backup/restore Cognee; corrección de la preparación anterior

La entrada 25-10 describía un bloqueo de preparación, ya resuelto mediante
ventana consistente autorizada. Backup set 20261025T222914Z-2e9b33c6; marker
062cfac7883306df2e5d13a92b6e8bf367dfe91049d0b184e26d9f027fceba41.
Confirmación autoritativa del operador: restore aislado 36/2226/6040, RTO
482,09 s, live Ready, recursos temporales eliminados. Snapshots y staging OCI
preservados. Corrección final: pg_restore por archivo tmpfs verificado y
exclusión únicamente de COMMENT - EXTENSION vector, conservando extensión
0.8.2 de postgres, restore como cognee y --exit-on-error.
Se incorporan contrato actualizado, helpers reutilizables, pruebas artificiales
y evidencia sanitizada; sin copiar launchers, dumps, modelos o logs de /tmp.
Este cierre no ejecuta sudo, backup, restore, reindexación ni cambios K3s.
RPO periódico, offsite y automatización no acreditados. Listos para iniciar MCP
como bloque separado, sin desplegarlo ni rebajar sus gates de auth/compatibilidad.

### 2026-10-26 — CHOMS Skills: promoción mínima Codex/Hermes

Perfil ECC v2.2.3 previamente revisado, hashes originales verificados y Git
limpio/sincronizado antes de editar. Copia canónica en tools/choms-skills con
licencia MIT, fuente fijada, hashes y seis adaptaciones. Solo se renombra la
skill MCP a choms-mcp-server-patterns; verification-loop queda bajo optional/.
Sin colisiones: doce enlaces individuales, seis por runtime, a los archivos
canónicos. Codex app-server skills/list detectó las seis habilitadas sin errores.
Hermes verificó listado, contenido parseado y expansión de seis slash commands;
no se habilitó el bundle skills ni skill_manage. Configuraciones, OAuth y las
cuatro herramientas MCP existentes no cambian. No se ejecutaron inferencias,
instaladores ECC, hooks ni código de las skills; memoria oficial sin cambios.
Kubernetes, Cognee, backups y repositorios privados permanecen fuera del alcance.
Evidencia sanitizada: tools/choms-skills/DISCOVERY_VALIDATION.json. Los enlaces
son reversibles y optional/ queda fuera de todas las raíces activadas.
La validación sensible detectó únicamente tres falsos positivos heredados del
tag OCI público en estos documentos. .gitleaks.toml conserva las reglas por
defecto y exceptúa solo el valor público exacto capturado por generic-api-key
en los tres archivos de contexto; no se reescribe el historial ni se excluyen
archivos completos u otros valores. Tres fixtures verifican la excepción,
la detección de claves sintéticas y el alcance por archivo.

### 2026-10-26 — CHOMS Skills 1.1.0: contexto y prompt caching propios

Se incorporan dos SKILL.md originales CHOMS, sin scripts ni referencias extra.
Context-budget limita lecturas a evidencia relevante y conserva checkpoints;
prompt-caching-strategy separa estable/variable sin asumir cache hit ni alterar
modelos o proveedores. No sustituyen validaciones, memoria o contratos de seguridad.
PROFILE/procedencia/hashes distinguen autoría propia de las adaptaciones ECC.
Las seis skills previas y verification-loop opcional se conservan sin cambios.
Activación mediante dos enlaces nuevos por runtime, sin sobrescrituras;
validación de descubrimiento/parseo 8/8 sin inferencias. Configuraciones intactas;
sin hooks, MCP, agentes, aprendizaje, servicios ni cambios Kubernetes.

### 2026-10-26 — OmniRoute runner-cli separado; gate de importación manual

Build oficial v3.8.52, commit ad6f33f66bda34eba98645d3bfdabbde294bc843,
target runner-cli sin alterar Dockerfile. Imagen principal b08a12e… preservada.
Codex 0.159.2/help/capability flags, UID 1000, amd64 y readyz loopback sin red:
PASS. Artefacto persistente verificado y SBOM de 837 componentes; no se afirma
escaneo CVE sin DB offline. Sidecar, configuración y PVC preparados sin aplicar.
Importador reutiliza el patrón CHOMS, verifica hash/espacio/identidad, importación
idempotente y alias digest CRI; requiere una sola elevación visible del operador.
No se ejecuta, no hay OAuth/PONG ni cambios K3s. Commit/push sujetos al cierre
operativo posterior. No se copian credenciales ni se modifican Codex/Hermes.

### 2026-10-26 — Corrección de estado y preparación overlay wreq-js

La importación fue confirmada por el operador; sidecar 2/2 Ready en node-02,
CODEX_HOME aislado autenticado con ChatGPT Plus y proveedor registrado.
La única prueba PONG devolvió 502. Se demostró que los loaders compilados son
contexts vacíos MODULE_NOT_FOUND, aunque require nativo y WS directo funcionan.
Overlay CHOMS de dos módulos en dos chunks, derivado de imagen oficial fijada
y contrastado con fuente v3.8.52/ad6f33f; sin reconstruir imagen. Hashes,
licencia, 16 pruebas offline y rollback documentados. NO aplicado; no nueva
inferencia, cambio OAuth/sidecar/clientes, commit ni push en este bloque.

### 2026-10-26 — OmniRoute codex-app-server operativo con overlay mínimo

Tras autorización explícita: hashes originales, dry-run servidor y diff final
limitado a ConfigMap inmutable, dos mounts subPath read-only y su volumen.
Rollout 2/2 Ready en node-02, cero reinicios; imágenes principal y sidecar
preservadas. Hashes montados coinciden; no aparece wreq-js import failed.
WS/initialize/account/read autenticado Plus y proveedor valid=true: PASS.
Una sola nueva solicitud cxa/gpt-6-sol: HTTP 200, contenido exacto PONG.
No se redirigen Codex/Hermes ni se copian credenciales locales. Overlay ligado
a la imagen fijada; rollback conserva sidecar, OAuth y claims. Backup de
CODEX_HOME y escaneo CVE siguen pendientes, sin afirmar cobertura acreditada.

### 2026-10-27 — CHOMS Memory Governance v1

Skill original, perfil 1.2.0; referencias de esquema/política y helper sintético
stdlib, sin DB/servicio nuevo. Consentimiento explícito frente a candidato
inferido, dedup, supersede, purga real en cola temporal, expiración y contexto
acotado. Regresión seguimos skill conserva el mínimo diseño/navegador/MCP/Figma/
Playwright/Image to Code/vídeo-social; ECC solo complementa. Tools/list real de
MCP 0.12.1 (17 tools), sin escrituras: ADR/index/trazas no cubren el contrato
central. Backend deshabilitado con error explícito; no se guardan datos reales.
Se añaden solo dos enlaces reversibles; configuraciones/allowlist Hermes y las
ocho skills previas permanecen intactas. Sin Kubernetes, OAuth ni inferencias.

### 2026-10-27 — Gate de purga lógica Ladybug aislado

Fuente oficial Ladybug v0.19.0/c934f673 y handler efectivo Cognee 1.6.5 fijados
por hashes. Allowlist añade tmp, wal.checkpoint y locks intent/apply; subgrafos
no registrados bloquean la operación. Compensación tras handler oficial, lstat,
raíz privada, exclusividad, estabilidad, fsync y reconciliación purge_pending.
27 tests offline PASS. Gate real autenticado sobre rol/esquemas temporales de
PostgreSQL existente, pgvector_shared y raíz de grafo propia: escritura/lectura/
búsqueda semántica local PASS; borrado sin contenido, vector, archivos ni caché;
tombstone opaca única; reinicio sin resurrección y doble forget PASS. Reproducción
real del handler deja shadow y wrapper lo retira. Limpieza del entorno completo;
Cognee/PostgreSQL Ready, sin memorias reales ni cambios de clientes. Se corrigieron
solo defectos del harness (orden imports, DB_PORT y señal PID 1). No borrado físico,
no backup/restore. MCP productivo completo aún pendiente; no se registra en clientes.

### 2026-10-27 — Corrección CI de falso positivo OCI preexistente

Actions de 0b77620: regresiones de purga PASS; Gitleaks detectó el tag público de
Cognee en cinco archivos cuyos blobs son idénticos a 7230418. Se amplía únicamente
la lista explícita de rutas del allowlist ya existente, conservando condición AND
y regex del valor exacto público. No se modifica ningún manifiesto ni secreto.
Se reproduce el escaneo completo de fuentes de CI con metadatos redactados.

### 2026-10-27 — CHOMS Memory v1 MCP interno y gate de backups

Se completa contrato independiente de ocho tools sobre PostgreSQL existente,
rol/esquema aislados, pgvector_shared y Ladybug privado. Purga validada sin cambios,
CAS, dedup, scopes, idempotencia, expiración, proyecciones reconciliables y tombstones
sin contenido. E2E nativo Codex/Hermes sin inferencias, carrera CAS, 401 inválido/
ausente, persistencia y no resurrección tras restart PASS. Limpieza exacta de 23
fixtures con comprobación de cero contenido/proyecciones/recibos/tombstones.
Se registra únicamente MCP nuevo con ocho tools en Hermes; Codebase allowlist,
OAuth y modelos intactos. ConfigMap inmutable y digest CRI del runtime ya importado,
Never, PVC Retain node-02, SA sin token, rootfs RO y NP solo PG/DNS.
Correcciones acotadas del harness: wrapper de error Hermes y batching de auditoría
20 IDs; resolución CRI por ID de configuración en vez de alias OCI no presente.
Cobertura backup completa/expiry NO acreditados; PVC nuevo sin captura y script
node-01 difiere de Git. Propuesta 7 días+24h no aplicada. Sin backup/restore/prune.
Memorias reales/captura OFF; seguimos skill no almacenada. Perfil 1.3.0 y runbook
con autorización explícita futura, rollback dry-run y límites de borrado lógico.

### 2026-10-29 — CHOMS Skills/MCP next: bloque local aislado

Base limpia 69a2f4b, fetch y divergencia 0/0 respecto a origin/main; trabajo solo
en feat/skills-mcp-next, sin merge. Perfil 1.4.0: cuatro módulos originales
preparados, nueve skills canónicas/optional intactas. Revisión y deduplicación
Emil/Impeccable/Taste/ECC/Browser/MCP/Find/design-guidelines/awesome-design-md/
Image to Code/Playwright/Figma, commits/licencias/hashes y lock npm.
Scripts locales para briefs, lint HTML, búsqueda offline, medición YUV por género,
exportación fit-and-pad sin sobrescritura y fixture/probe MCP sin persistencia.
Codex discovery 13/13 y parser Hermes nativo 13/13, sin catálogo/slash completo.
Veinte comprobaciones browser, smoke Agent Browser/playwright-cli y MCP Playwright
25 tools/about:blank/cierre PASS. Media sintética medida/exportada y verificada.
Excepción Chromium sin sandbox solo en fixtures por restricción del host.
Figma initialize anónimo 401: gate OAuth real, sin credenciales ni archivos.
Dos nombres sin fuente, confirmados por usuario: identificación pendiente,
no activados ni cubiertos; contrato CHOMS separado. Sin redistribuir contenido
Vercel agent-skills al no acreditar licencia por archivo. Detalles y verificaciones
finales en tools/choms-skills/NEXT_VALIDATION.json. No activación global en este host
(cero enlaces CHOMS), cambios Memory, producción, OAuth ni publicación social.
No se consulta salud ni drift Kubernetes por aislamiento; cierre Git solo contra
la rama autorizada. Dependencias de prueba portables bajo /tmp, sin upgrades del sistema.

### 2026-10-29 — Integración Skills/MCP y activación node-dev-02

Autorización posterior sustituye el límite previo de no merge: origin/main sigue
en 69a2f4b, rama 04d7036 limpia y 0/0 remota al inicio. Diff completo sin rutas
protegidas y nueve skills canónicas/optional intactas. Perfil 1.4.1; 26 enlaces
reversibles sin sobrescritura, herramientas fijadas persistidas en usuario.
Codex real desde raíz de usuario 13/13; Hermes skills_list, skill_view completo y
expansión slash nativa 13/13, sin chat/modelos/gateway. Aviso Hermes por symlinks
fuera de raíz conservado, destinos verificados y sin relajar confianza; plugins
auth opcionales sin httpx fuera del subsistema probado. Browser 20 checks PASS;
25 tests incluyendo colisiones y rollback, integridad y Gitleaks acotado sin hallazgos.
Se prepara merge trazable y push normal a main, sin modificaciones a servicios,
Memory, Kubernetes, Terraform, Restic, NAS, OmniRoute, secretos o publicación social.
MCP Playwright conserva uso local bajo demanda sin registro global; Figma queda
preparado pendiente de intervención OAuth. Dos nombres no identificados siguen
sin activar ni cubrir. Detalle actual en ACTIVATION_VALIDATION.json; recibos previos
conservados. Salud/drift productivos no consultados por aislamiento expreso.

### 2026-10-29 — Cierre OAuth Figma nativo

Confirmación del operador; main d8b7dbd limpio y 0/0 tras fetch. Faltaba la entrada
persistente (el login anterior usó override); añadida únicamente URL oficial y
enabled=true en config nativa, resto semánticamente intacto y sin tocar credenciales.
Tres procesos Codex app-server nuevos conectan con OAuth y sin override/login:
Figma MCP Server 1.0.0, capabilities tools/resources/prompts, 45 tools (26 read-only
anotadas) y 121 recursos. whoami {} devuelve éxito, identidad descartada; get_metadata
sobre clave sintética inexistente devuelve el rechazo esperado. No se acredita
lectura de diseño real ni se crea fixture remoto. Catálogo y recibo agregados sin
cuerpos de respuesta, tokens o datos de usuario en FIGMA_VALIDATION.json.
Desactivación por enabled=false o retirada de esa única entrada con mcp remove,
sin logout/restauración global. Templates portables conservados inertes. Solo
cambia evidencia/documentación/catalogación del perfil y SHA256SUMS; sin scripts,
skills canónicas, modelos, Hermes OAuth, Memory, producción o servicios permanentes.
Validaciones de integridad, diff y Gitleaks acotado requeridas antes de publicar.
