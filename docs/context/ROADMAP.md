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
| Resolve Scrutiny collector device isolation prerequisite (`SEC-002`) | `blocked` | Select and validate a K3s/containerd-supported device-plugin, CDI, DRA or equivalent stable block-device mapping that creates per-device cgroup rules. The review found no candidate with demonstrable compatibility, security and maintenance; the current design and residual risk are temporarily accepted. A future host-service collector is a separate architectural block. Current hostPath mounts cannot replace privileged device access; do not proceed to `SEC-003` as part of this block. |

## High priority

| Work | Status | Closure criteria |
|---|---|---|
| MetalLB speaker reconciliation | `blocked` | Runtime was safely rolled back to `v0.15.2` after persistent memberlist-join failures and immutable-node `ServiceL2Status` conflicts. Keep the matching digest in Git; do not retry until node-to-node TCP/UDP 7946 connectivity and status ownership are understood and the separate diagnosis closure criteria are satisfied. |
| MetalLB speaker memberlist/L2 diagnosis | `blocked` | Suspended pending privileged node readings by an authorized platform operator. Determine the intended TCP/UDP 7946 path, explain immutable `ServiceL2Status` ownership, prove 3/3 convergence and `/metrics` scraping, and only then plan a separate speaker rollout. |
| Scrutiny collector hardening | `blocked` | Digest and resource boundaries are complete. Privilege reduction is blocked because non-privileged hostPath devices remain denied by containerd's device cgroup even with all capabilities; resume only with an approved per-device mapping mechanism. |
| Scrutiny server privilege reduction | `completed` | `SEC-003` separated pinned Scrutiny web/API 0.8.2 and InfluxDB 2.2.0, removed server device privilege, and added the third Kubernetes collector on S. SQLite writes, restart persistence, 11 active devices and final backup/restore passed. |
| Jellyfin device-access design | `pending` | Prove hardware transcoding with non-privileged, narrowly mapped devices; preserve library access and playback; document rollback. |
| Independent/off-site backup copy | `pending` | Produce an encrypted copy outside the live NAS failure domain and complete a documented restore validation. |
| NAS mdraid local monitoring | `completed` | Versioned systemd drop-ins add syslog delivery without modifying the array. The permanent monitor is active; the oneshot preserves its vendor `AUTOSCAN` environment and conditional execution and completes successfully. External critical delivery through Alertmanager is now completed separately. |

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
| Raspberry Pi external monitor phase 1 | `completed` | One lightweight ARMv7 container checks representative external DNS/HTTPS/TLS/status/latency and restricted RP3 host signals with persistent three-failure alert state and independent Git-free Telegram credentials. HTTP and host-root false positives are resolved. The monitor is healthy with zero restarts; `rp3-local` intentionally remains firing for real current/historical undervoltage and throttling `0x50005` pending a 5.1 V / 2.5 A supply and short low-resistance micro-USB cable, followed later by a controlled reboot. |
| Alertmanager Telegram critical delivery | `completed` | The locked monitoring release references and mounts an external Git-free Secret. Critical firing and resolved delivery passed with a real synthetic alert; Watchdog, warning and unmatched alerts remain on `null`. The reusable interactive script supports creation and rotation without exposing credentials. |
| Traefik Gateway Shim warning correction | `completed` | Reconciled the user-supplied Helm values to the live release and removed only the obsolete issuer annotation. The manual Certificate remained Ready at revision 6, Traefik stayed 2/2, Gateway status and HTTPS consumers passed, and the warning did not recur. |
| Kubernetes backup and recovery automation | `completed` | Versioned automation and successful controlled Nextcloud restore test; `b5b8792`. |
| Filebrowser image pinning (`IMG-003`) | `completed` | Pinned the exact effective digest only; validated route, native authentication path, storage mounts, consumer health and drift zero in the 2026-08-19 rollout. |
| Home image pinning (`IMG-001`) | `completed` | Pinned the exact effective digest only; validated two replicas, route/auth response, ConfigMap metadata, mounted files, consumer health and controller drift zero in the 2026-08-19 rollout. |
| Scrutiny cold-bootstrap recovery prerequisite | `completed` | Manual mode-0700 NAS copy from stopped InfluxDB/SQLite state, atomic publication, checksums, offline integrity validation and isolated Scrutiny 0.8.2/InfluxDB 2.2.0 startup passed on 2026-08-21. The server interruption was 83 seconds and all temporary resources were removed. This does not complete recurring RPO-24-hour backup or `SEC-003`. |
| Scrutiny backup authorization bootstrap | `completed` | Official offline InfluxDB 2.2.0 operator recovery created one dedicated runtime authorization and stored only its token and ID in `monitoring/scrutiny-backup-influx-operator` through a closed stdin pipeline. Authentication, workload health, cleanup and drift passed; no recurring backup or `SEC-003` change was made. |
| Scrutiny recurring logical backup prerequisite | `completed` | Daily official InfluxDB backup plus transactional SQLite backup publish atomically to protected NAS storage with checksums, locks and 7/8/12/5 GFS. A manual backup and full isolated restore passed on 2026-08-22; the bootstrap copy was preserved and `SEC-003` remains pending. |
| Scrutiny Hub/Spoke migration (`SEC-003`) | `completed` | Web/API has no privilege, devices, udev, hostPort, Influx tree or ServiceAccount token. Three Kubernetes collectors plus NAS cover 11 active unique devices while one July record remains historical. |
| NAS Scrutiny collector digest pinning | `completed` | Replaced only the mutable v0.8.2 collector reference with its already-running digest. The NAS collector retained its runtime contract, completed five reads and publications, and remained disjoint from the six active Kubernetes devices. No Kubernetes, privilege, mount, schedule or native-service change was made. |
| MariaDB hardening | `completed` | Digest, Recreate, probes, healthy consumer; `2948d31`. |
| Nextcloud secure sharing | `completed` | Reproducible enforced policy and isolated E2E cleanup confirmed; `c16fd81` plus runtime evidence. A detailed historical HTTP transcript was intentionally not retained. |
| Workload audit | `completed` | Full inventory and repeatable read-only script; `3d10730`. |
| Kubernetes security baseline | `completed` | Non-mutating repository and safe edge audit with explicit runtime limitations and prioritized backlog; [`KUBERNETES_SECURITY_BASELINE_2026-08-17.md`](../audits/KUBERNETES_SECURITY_BASELINE_2026-08-17.md). |
| Prometheus route protection | `completed` | `SEC-001`: namespaced Authelia ForwardAuth and a minimal `one_factor` policy protect the Prometheus HTTPRoute; anonymous redirect, resolved references, internal readiness, targets, Grafana health, routes, cluster health, and drift zero validated. |
| IAM and observability evidence block | `completed` | Evidence phase of `IAM-001`, plus `IAM-002` and `OBS-003`: all managed identities, effective high-risk permissions, monitor resources, 24 active targets, and the MetalLB discovery/reachability split documented in the [audit](../audits/KUBERNETES_IAM_OBSERVABILITY_AUDIT_2026-08-17.md). |
| Portainer IAM-001 access diagnosis | `completed` | Read-only ownership, use-evidence, exposure and three-profile analysis documented in the [Portainer IAM diagnosis](../audits/PORTAINER_IAM_001_DIAGNOSIS_2026-08-17.md); no Kubernetes change. Profile A was subsequently selected and implemented. |
| Portainer IAM-001 viewer migration | `completed` | Platform owner selected Profile A; explicit versioned viewer RBAC preserves inventory, events, metrics and Pod logs while denying Secrets, writes, interactive Pod access, tokens, RBAC delegation, CRD and webhook mutation. Staged isolated and real-identity matrices passed; the old `cluster-admin` binding is absent. Authenticated UI review remains pending. |
| Scrutiny collector digest pinning | `completed` | `SUP-001`: both expected collectors previously resolved `v0.8.2-collector` to the same digest; Git and the DaemonSet now declare that digest. RollingUpdate preserved 2/2 availability, sanitized device counts and server ingestion; final drift is zero. Probes, resources and privileges remain separate pending work. |
| Scrutiny collector resource boundaries | `completed` | `RES-002`: seven days of metrics justified `10m`/`32Mi` requests and `250m`/`128Mi` limits. No reliable v0.8.2 collector health signal exists, so probes are explicitly not applicable. The sequential rollout preserved two devices per collector and ingestion. `SEC-002` and `SEC-003` remain pending. |
| Redis hardening | `completed` | Recreate, probes, justified resources, digest, consumers healthy; `fc3df18`. |
| PostgreSQL reconciliation | `completed` | Published digest reconciled and validated; runtime-only, no empty commit. |
| MetalLB controller reconciliation | `completed` | Published digest reconciled; webhook, speakers, VIP, routes, and cluster validated; runtime-only. |

## Deferred

| Work | Status | Closure criteria |
|---|---|---|
| Email platform, MX/SPF/DMARC/PTR, and mail-related router changes | `deferred` | Remains untouched until explicit authorization and a dedicated design covering provider constraints, DNS, deliverability, security, backup, and rollback. |

## Colegio staging checkpoints

| Work | Status | Closure criteria |
|---|---|---|
| Colegio staging foundation (Checkpoint 1) | `completed` | Web, split DNS, certificate SANs and Authelia ForwardAuth deployed and committed independently; later Moodle/Gibbon failures do not roll back this checkpoint. |
| Moodle activities and recovery (Checkpoint 2) | `completed` | Official assign defaults, fictional activity persistence, CronJob, ClusterIP/HTTPRoute ForwardAuth, logical backup and isolated restore passed; artificial restore marker documented. |
| Gibbon installer (Checkpoint 3 declarative) | `completed` | Pinned bootstrap image, independent MariaDB/PVC/Secret, ClusterIP Service and Authelia-protected HTTPRoute deployed; official manual installer is available and remains intentionally incomplete. |
