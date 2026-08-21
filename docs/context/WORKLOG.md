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
