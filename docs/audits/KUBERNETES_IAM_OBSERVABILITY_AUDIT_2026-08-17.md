# Kubernetes IAM and Observability Audit — 2026-08-17

## Scope and outcome

This non-mutating audit completes the evidence block `IAM-001`, `IAM-002`, and
`OBS-003`. It correlates Git at
`d9c0dbfd2133bd60d32e0b35a458d3779a428b69`, live controller templates,
effective RBAC, Prometheus Operator resources, targets, Services,
EndpointSlices, and safe metrics/health checks. No Kubernetes resource, Helm
release, workload, network rule, route, Secret, or node was changed.

At both the initial and repeated checks, all three nodes were Ready, no Pod was
Pending or Failed, Prometheus was Ready, 24 targets were up, zero were down,
and `Watchdog` was the only firing alert.

No Critical finding was established. The High finding is the public
administration workload Portainer receiving unversioned `cluster-admin`.
Several chart workloads have demonstrably broader Secret-read scope than their
current consumers require. Prometheus has healthy core coverage but does not
discover annotated workloads without a ServiceMonitor or PodMonitor.

## Methodology and safety boundaries

- Read repository instructions, active memory, security/workload audits, ADRs,
  direct manifests, locked Helm values, and the vendored MetalLB v0.15.2
  manifest.
- Queried Deployments, StatefulSets, DaemonSets, CronJobs, recurrent Jobs,
  ServiceAccounts, bindings, referenced roles, Pod templates, and projected
  token volumes. No persistent or recurrent Job was present.
- Expanded effective rules with `kubectl auth can-i --list` for every nontrivial
  workload ServiceAccount and used targeted positive and negative `can-i`
  checks for high-risk permissions.
- Queried only Secret names or `secretKeyRef` metadata where necessary; no
  Secret data or token was requested.
- Queried the Prometheus CR, monitor CRs, Services, EndpointSlices, active and
  dropped target aggregates, CRD conditions, operator errors, and events.
- Tested MetalLB metrics from the Prometheus Pod network and through the API
  proxy without printing addresses or metric payloads.
- Repeated the Portainer, target-count, monitor-count, and MetalLB speaker
  checks before documenting conclusions.

Limitations:

- `can-i` proves authorization, not that an application exercises every
  permission.
- No authenticated Portainer workflow was exercised, so its minimum functional
  management scope must be captured before replacement RBAC is enforced.
- Dropped targets were aggregated by scrape pool; their endpoint addresses and
  topology-bearing labels were intentionally not retained.
- No test Pod, ephemeral container, package, or network rule was introduced.

## Inventory summary

- Managed workload controllers: 35 — 17 direct, 15 Helm, and 3 K3s-managed.
- Controller kinds: Deployments, StatefulSets, and DaemonSets. No active
  CronJob or persistent/recurrent Job was present.
- Workloads using `default` ServiceAccount: 14.
- Running Pods with a projected ServiceAccount token: all Pods except Loki
  canary, Loki gateway, and node-exporter.
- Explicit workload ServiceAccounts: cert-manager components, K3s system
  components, Alloy, Loki, MetalLB, monitoring stack, NFS provisioner,
  Portainer, and Traefik.
- Privileged Linux containers: Jellyfin, Scrutiny server, and Scrutiny
  collector. This is container privilege, not Kubernetes RBAC.
- Host access: Jellyfin, Scrutiny roles, qBittorrent, and node-exporter use
  hostPath; MetalLB speaker and node-exporter use host networking;
  node-exporter uses host PID; speaker adds `NET_RAW`.
- NetworkPolicies: zero. This does not grant Kubernetes API permissions, but it
  leaves east-west traffic without a Git-defined allowlist.

## Workload identity matrix

`Default` automount means the template does not override Kubernetes' default.
`Token` records an observed projected token volume, not token contents.

| Namespace | Workload | Owner | ServiceAccount | Automount | Token | API need / evidence |
|---|---|---|---|---|---|---|
| apps | Deployment/choms-controller | Direct | `default` | Default | Yes | No API client or binding found |
| apps | Deployment/home | Direct | `default` | Default | Yes | No API client or binding found |
| apps | Deployment/nextcloud | Direct | `default` | Default | Yes | No API client or binding found |
| apps | Deployment/portainer | Direct | `portainer` | Default | Yes | Cluster administration; exact required scope not documented |
| apps | Deployment/uptime-kuma | Direct | `default` | Default | Yes | No API client or binding found |
| cert-manager | Deployment/cert-manager | Helm | `cert-manager` | Default | Yes | Certificates, issuers and leader election |
| cert-manager | Deployment/cert-manager-cainjector | Helm | `cert-manager-cainjector` | Default | Yes | Injects CA data and uses leader election |
| cert-manager | Deployment/cert-manager-webhook | Helm | `cert-manager-webhook` | Default | Yes | Admission review and serving-certificate lifecycle |
| databases | Deployment/mariadb | Direct | `default` | Default | Yes | No API client or binding found |
| databases | Deployment/postgres | Direct | `default` | Default | Yes | No API client or binding found |
| databases | Deployment/redis | Direct | `default` | Default | Yes | No API client or binding found |
| filebrowser | Deployment/filebrowser | Direct | `default` | Default | Yes | No API client or binding found |
| kube-system | Deployment/coredns | K3s | `coredns` | Default | Yes | Watches DNS-related Kubernetes state |
| kube-system | Deployment/local-path-provisioner | K3s | Dedicated | Default | Yes | Provisions PVs and watches nodes/PVCs |
| kube-system | Deployment/metrics-server | K3s | `metrics-server` | Default | Yes | Reads node and Pod metrics |
| logging | DaemonSet/choms-alloy | Helm | `choms-alloy` | Default | Yes | Discovers Pods and cluster events |
| logging | StatefulSet/choms-loki | Helm | `choms-loki` | True | Yes | Rule sidecar watches labeled resources |
| logging | DaemonSet/choms-loki-canary | Helm | Dedicated | False | No | No API need |
| logging | Deployment/choms-loki-gateway | Helm | Dedicated | False | No | No API need |
| media | Deployment/jellyfin | Direct | `default` | Default | Yes | No API client or binding found; Linux privilege is separate |
| media | Deployment/threadfin | Direct | `default` | Default | Yes | No API client or binding found |
| metallb-system | Deployment/controller | Vendored | `controller` | Default | Yes | Services, MetalLB CRs, webhook and status management |
| metallb-system | DaemonSet/speaker | Vendored | `speaker` | Default | Yes | Services/endpoints/nodes and L2 status |
| monitoring | Deployment/Grafana | Helm | Dedicated | True | Yes | Dashboard and datasource sidecars |
| monitoring | Deployment/kube-state-metrics | Helm | Dedicated | True | Yes | Watches selected Kubernetes object metadata |
| monitoring | Deployment/Prometheus Operator | Helm | Dedicated | True | Yes | Reconciles monitoring CRs and generated configuration |
| monitoring | StatefulSet/Alertmanager | Operator | Dedicated | True | Yes | No explicit binding; token not demonstrated necessary |
| monitoring | StatefulSet/Prometheus | Operator | Dedicated | True | Yes | Kubernetes service discovery and metrics access |
| monitoring | DaemonSet/node-exporter | Helm | Dedicated | False | No | Host metrics; no Kubernetes API need |
| monitoring | Deployment/scrutiny | Direct | `default` | Default | Yes | No API client or binding found; host access is separate |
| monitoring | DaemonSet/scrutiny-collector | Direct | `default` | Default | Yes | No API client or binding found; device access is separate |
| nfs-provisioner | Deployment/NFS provisioner | Helm | Dedicated | Default | Yes | PV/PVC provisioning and leader election |
| qbittorrent | Deployment/qBittorrent | Direct | `default` | Default | Yes | No API client or binding found; hostPath is separate |
| security | Deployment/authelia | Direct | `default` | Default | Yes | No API client or binding found |
| traefik | Deployment/Traefik | Helm | `traefik-k8s` | True | Yes | Gateway/CRD discovery, Services, endpoints and TLS metadata |

The 14 `default`-SA workloads are choms-controller, home, Nextcloud, Uptime
Kuma, MariaDB, PostgreSQL, Redis, Filebrowser, Jellyfin, Threadfin, Scrutiny
server, Scrutiny collector, qBittorrent, and Authelia. Targeted checks proved
that representative `default` SAs cannot read Pods or Secrets or create
`pods/exec`; nevertheless, their unused projected tokens remain avoidable
credential material.

## Effective RBAC and high-risk permission matrix

| Identity | Effective evidence | Assessment | Correct source | Minimum later change |
|---|---|---|---|---|
| `apps/portainer` | Runtime ClusterRoleBinding `portainer` grants `cluster-admin`; `can-i` confirms `*.*`, Secret access, exec, token creation, impersonate, bind and escalate | **High; excessive and unversioned** | `stacks/kubernetes/apps/portainer.yaml` | Inventory intended Portainer actions, version a dedicated role/binding, then remove only the old binding after functional tests |
| `logging/choms-alloy` | Cluster-wide Secret list/watch; Git config uses only Pod discovery and events | **Medium; no current Secret consumer** | `stacks/kubernetes/logging/alloy/values.yaml` | Constrain chart RBAC to Pods/nodes/events required by the deployed config |
| `monitoring/Grafana` | Cluster-wide Secret list/watch; sidecars use `RESOURCE=both`, but every matching dashboard/datasource source is a ConfigMap in `monitoring` | **Medium; broader kind and namespace than current consumers** | `stacks/kubernetes/monitoring/values.yaml` | Restrict sidecars to ConfigMaps and `monitoring`, verify dashboard/datasource reconciliation |
| `logging/choms-loki` | Cluster-wide Secret list/watch; rule sidecar uses `RESOURCE=both`, with zero labeled rule sources | **Medium; unneeded for current state** | `stacks/kubernetes/logging/loki/values.yaml` | Disable unused rule discovery or restrict it to local ConfigMaps |
| `monitoring/kube-state-metrics` | Lists/watches Secrets cluster-wide because `secrets` is in `--resources`; no active rule or dashboard references `kube_secret_*` | **Medium; current consumers do not justify it** | `stacks/kubernetes/monitoring/values.yaml` | Remove the Secret collector through supported chart values, then validate rules and dashboards |
| Prometheus Operator | `*` on Secrets and monitoring resources | High-impact but **justified upstream controller scope** for generated configuration; no excess established | Monitoring Helm values/chart | Retain until a chart-supported namespace-scope design is separately proven |
| cert-manager controller | Secret create/update/delete and certificate writes | High-impact but **functionally required** for certificate lifecycle | cert-manager locked Helm workflow | Retain; validate only through a cert-manager-specific audit |
| Traefik | Cluster-wide Secret list/watch plus Gateway/CRD reads | High-impact but required for current multi-namespace routing and TLS; no excess established | Traefik locked Helm values | Review only with the route/TLS ownership model |
| MetalLB controller/speaker | Controller manages memberlist/webhook/CRDs; speaker reads its namespace Secrets and has wildcard status verbs | High-impact but matches the vendored v0.15.2 policy and current consumers | Vendored MetalLB manifest | Do not change while speaker is blocked |
| NFS provisioner | Creates/deletes PVs and watches nodes/PVCs | High-impact but required for dynamic provisioning | NFS locked Helm values | Retain unless storage lifecycle is redesigned |
| Broad groups | `system:masters` has cluster-admin; authenticated/unauthenticated groups receive only standard discovery/public-info roles | **Informational; standard control-plane bindings** | K3s lifecycle | No direct-manifest change |

No application `default` ServiceAccount had an explicit RoleBinding or
ClusterRoleBinding. All receive standard authenticated discovery permissions.
No unbound namespaced Role was found. The unbound cert-manager `view`, `edit`,
and cluster-view ClusterRoles are intentional aggregation roles, not orphan
controller permissions.

Several bindings reference K3s controller identities that are not stored as
ServiceAccount objects. Those controllers authenticate as control-plane users
or virtual identities; they are not evidence of a broken workload subject.
Unused namespace-default SAs and the chart-created Loki memcached SA have no
binding or workload impact and are Informational cleanup only.

## Git/runtime reconciliation

- **Material drift:** the runtime `portainer` ClusterRoleBinding to
  `cluster-admin` is absent from Git. Git versions the ServiceAccount and
  workload reference but not its authority.
- MetalLB ServiceAccounts, bindings and high-risk rules match the vendored
  v0.15.2 manifest; its speaker runtime image declaration remains the known
  blocked tag/digest exception.
- Monitoring, cert-manager, Loki, Alloy, NFS and Traefik RBAC is Helm-generated.
  Corrections must use their locked, versioned values; rendered RBAC must not be
  edited.
- Prometheus selectors match Git: empty ServiceMonitor, PodMonitor and Probe
  selectors intentionally select all matching resources across namespaces.
- Alloy's ServiceMonitor matches its versioned value. The other active
  ServiceMonitors are generated by the monitoring chart.

## Prometheus discovery and coverage

The Prometheus CR has no `additionalScrapeConfigs` reference. Runtime contains
10 ServiceMonitors, zero PodMonitors, and zero Probes. All 24 active targets are
up and none are down. Dropped targets are expected selector/relabel rejections
inside each scrape pool, not failed scrapes.

| Component | Expected mechanism | Declarative/runtime resource | State | Cause / correct source | Priority |
|---|---|---|---|---|---|
| Prometheus | ServiceMonitor | Chart-generated self monitor, two endpoints | Up 2/2 | Expected | Informational |
| Alertmanager | ServiceMonitor | Chart-generated self monitor, two endpoints | Up 2/2 | Expected | Informational |
| Grafana | ServiceMonitor | Chart-generated monitor | Up 1/1 | Expected | Informational |
| kube-state-metrics | ServiceMonitor | Chart-generated monitor | Up 1/1 | Expected | Informational |
| node-exporter | ServiceMonitor | Chart-generated monitor | Up 3/3 | Expected host metrics | Informational |
| Kubernetes API | ServiceMonitor | Chart-generated apiserver monitor | Up 1/1 | Expected | Informational |
| Kubelet/cAdvisor/probes | ServiceMonitor | Chart-generated kubelet monitor | Up 9/9 | Three endpoints per node | Informational |
| CoreDNS | ServiceMonitor | Chart-generated monitor | Up 1/1 | Expected | Informational |
| Prometheus Operator | ServiceMonitor | Chart-generated monitor | Up 1/1 | Expected | Informational |
| Alloy | ServiceMonitor | `logging/alloy/values.yaml` | Up 3/3 | Expected | Informational |
| Traefik | ServiceMonitor | Annotation and metrics port exist; no ServiceMonitor/metrics Service | Absent | Operator does not consume annotations; change Traefik values only | Medium |
| cert-manager | ServiceMonitor | Three annotated workloads and metrics Services; no ServiceMonitor | Absent 3 | Operator does not consume annotations; change cert-manager values only | Medium |
| MetalLB controller | ServiceMonitor or PodMonitor | Annotated Pod, no metrics Service/monitor | Absent | No discovery object; endpoint reachable from Prometheus | Medium |
| MetalLB speaker | ServiceMonitor or PodMonitor | Three annotated hostNetwork Pods, no metrics Service/monitor | Absent | No discovery object; only 1/3 endpoints reachable from Prometheus | Blocked |
| Loki and canary/gateway exporter | ServiceMonitor | Metrics ports/Services exist; no monitor | Absent | Loki values do not enable self-monitoring resources | Medium |
| NFS provisioner | Exporter/ServiceMonitor if supported | No declared metrics port or monitor | Not exposed | Health is not a Prometheus endpoint; requires capability design | Low / needs evidence |
| MariaDB, PostgreSQL, Redis | Dedicated exporters if justified | Database ports only; no metrics endpoints | Not exposed | Never scrape database protocol ports as Prometheus | Medium design gap |
| Direct applications | App-native metrics only where supported | No declared Prometheus metrics endpoints | Not expected | Web/health endpoints are not automatically metrics | Informational |

## MetalLB speaker root cause

Established facts:

1. The only MetalLB Service is the controller webhook Service; it does not
   expose metrics.
2. Controller and speaker Pods declare port `monitoring` on 7472 and carry
   `prometheus.io/scrape` annotations.
3. There is no MetalLB ServiceMonitor or PodMonitor, and Prometheus has no
   annotation-based additional scrape configuration. Therefore no controller
   or speaker target is generated. This is the exact discovery cause.
4. Controller metrics are reachable through both the API proxy and the
   Prometheus Pod network.
5. Speaker native `/metrics` probes pass, but repeated tests from the
   Prometheus Pod network reached only one of three hostNetwork endpoints. API
   proxy tests also reached only one of three, not consistently the same
   perspective. There is no NetworkPolicy.
6. No metrics-related error appeared in recent controller or speaker logs.

The ordered speaker hypotheses are:

1. **Confirmed discovery gap:** no Service/monitor resource means Prometheus
   never attempts a scrape.
2. **Confirmed cross-node reachability gap:** a future monitor would still see
   two speaker endpoints fail from the current Prometheus placement.
3. **Inference:** hostNetwork plus node firewall/routing behavior is the likely
   layer for the reachability asymmetry. Bind restriction is less likely
   because kubelet probes pass and one remote perspective succeeds, but the
   exact bind address was not independently read from the process socket.

This is distinct from memberlist: metrics uses TCP/7472 while memberlist uses
TCP/UDP 7946 and also has `ServiceL2Status` ownership errors. Both gaps may
share a node-network cause, but that is an inference, not an established fact.
Speaker rollout and monitoring remediation remain Blocked until the existing
network/status investigation is authorized and completed.

## Prioritized findings

### Critical

None established.

### High

1. Portainer has unversioned `cluster-admin`, including Secrets, exec, token
   creation, impersonation, bind, and escalate. Compromise of its public admin
   surface would provide full cluster control.

### Medium

1. Fourteen direct workloads use `default` SA with projected tokens but no
   demonstrated API need.
2. Alloy can list/watch Secrets cluster-wide although its versioned config only
   discovers Pods and events.
3. Grafana sidecars can watch Secrets cluster-wide although all current labeled
   inputs are ConfigMaps in `monitoring`.
4. Loki's rule sidecar can watch Secrets cluster-wide although no labeled rule
   source exists.
5. kube-state-metrics watches Secrets, while no active rule or dashboard uses
   its Secret metrics.
6. Traefik, cert-manager, Loki and MetalLB expose or declare metrics but lack
   matching monitors; database monitoring requires dedicated exporters rather
   than health or protocol endpoints.

### Low

1. Several unused default/chart ServiceAccounts have neither workload nor
   binding consumers.
2. NFS metrics capability and direct-application metrics remain needs-evidence
   items, not proven outages.

### Informational / false positives discarded

- Linux privilege, hostPath, hostNetwork and device access are not RBAC.
- Standard discovery roles for authenticated identities are not cluster-admin.
- K3s controller bindings to virtual/user identities are not missing workload
  ServiceAccounts.
- cert-manager aggregation roles are intentionally unbound.
- Health endpoints and generic HTTP pages are not Prometheus metrics endpoints.
- Zero PodMonitors/Probes is not itself a defect while ServiceMonitors cover the
  intended targets.

## Exact remediation order

Each step is a separate future change; this audit authorizes none of them.

1. **Portainer only:** capture the exact management operations in use, version
   a minimum dedicated ClusterRole/Binding, validate those operations and
   negative high-risk checks, then remove only the old cluster-admin binding.
   Rollback: restore the reviewed binding. RBAC-only change should not restart
   the Pod, but loss of administration is possible.
2. **Alloy only:** use supported chart values to remove Secret access while
   preserving Pod discovery, event collection and Loki ingestion. Rollback:
   atomic Helm rollback.
3. **Grafana only:** restrict sidecars to ConfigMaps in `monitoring`; validate
   every dashboard and datasource. Rollback: atomic Helm rollback.
4. **Loki only:** disable unused rule sidecar discovery or restrict it to local
   ConfigMaps; validate ingestion and queries. Rollback: atomic Helm rollback.
5. **kube-state-metrics only:** remove the Secret collector; prove rules,
   dashboards and target health. Rollback: atomic Helm rollback.
6. **Direct workloads, one at a time:** disable token automount only after API
   independence is proven, beginning with a stateless low-risk workload.
7. **cert-manager, Traefik and Loki separately:** add chart-supported monitors
   only after endpoint, labels and useful consumer queries are defined.
8. **MetalLB controller/speaker:** remain outside autonomous execution. Design
   discovery only after speaker TCP/7472 reachability and the separate
   TCP/UDP 7946 plus `ServiceL2Status` blockers are resolved.

## Acceptance and conceptual rollback

- RBAC changes: preserve every demonstrated operation; add negative `can-i`
  tests for Secrets, exec, token creation, impersonate, bind and escalate;
  restore only the prior reviewed binding on failure.
- Helm RBAC changes: locked plan, exact rendered diff, atomic apply, workload
  and consumer validation, then effective `can-i` confirmation; use Helm
  rollback on failure.
- Monitoring changes: monitor Accepted by the operator, expected endpoints only,
  targets up across several cycles, no duplicate series, stable rules/alerts,
  and no topology or Secret labels exposed; remove the new monitor or atomically
  roll back its release on failure.
- MetalLB: require 3/3 speaker metrics reachability before creating an active
  monitor; never use a monitoring rollout to diagnose memberlist.
