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
