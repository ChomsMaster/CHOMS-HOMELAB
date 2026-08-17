# Portainer IAM-001 Diagnosis — 2026-08-17

## Scope and outcome

This read-only diagnosis determines what can be established about the
Kubernetes access required by Portainer CE 2.39.5. It changed no Kubernetes
resource, workload, route, storage, identity, authorization policy, or Secret.
It did not authenticate to Portainer or inspect its database or PVC contents.

The current ServiceAccount has unrestricted `cluster-admin`, but no retained
evidence demonstrates that Portainer has used write, Secret, exec, RBAC,
impersonation, token-issuance, node-administration, storage-administration,
CRD, or webhook permissions. The safest provisional profile that preserves
the demonstrated inspection function is Profile A, a Secret-free read-only
viewer. This is a proposal, not authorization to change RBAC.

## Methodology and limitations

- Correlated Git, all reachable Git history, runtime metadata, targeted
  `kubectl auth can-i` checks, recent events, sanitized log counts, route and
  endpoint status, and aggregate Prometheus API evidence.
- Queried no Secret object or value. No usernames, sessions, cookies, tokens,
  addresses, PVC data, or Portainer database data were read or retained.
- Kubernetes audit logging was absent or unreadable and was not enabled.
- Runtime objects do not retain useful `managedFields`; creator attribution is
  therefore unavailable.
- No authenticated Portainer workflow was permitted. `can-i` proves available
  authority, not historical use. Empty evidence is not evidence that a
  function was never used.
- The Prometheus query for requests attributed to the Portainer ServiceAccount
  returned no series. This does not prove inactivity because the API-server
  metric may not carry that identity label.

## Initial health

Git was clean on `main`, equal to `origin/main`, with divergence `0/0` at
`5bd5464d58bdcb10ed3112132968b3a4b97c79b7`. Three nodes were Ready and no Pod
was Pending or Failed. Portainer, Authelia, and Traefik were Ready; the
Portainer Pod had zero restarts; its PVC was Bound; and its Service endpoint
was Ready. The HTTPRoute reported `Accepted=True` and `ResolvedRefs=True` for
both listeners.

## Ownership and exact drift

| Object | Observed ownership | Git state | Assessment |
|---|---|---|---|
| ServiceAccount `apps/portainer` | Direct object; no owner reference | Present in `stacks/kubernetes/apps/portainer.yaml` | Git-owned identity |
| Deployment `apps/portainer` | Direct object; no owner reference | Present in the same manifest | Direct, not Helm/operator-managed |
| Service and PVC | Direct objects; no owner references | Present in the same manifest | Direct desired state |
| ClusterRoleBinding `portainer` | Direct object; no owner reference; points to `cluster-admin` and `apps/portainer` | Absent from Git and all reachable history | Material unversioned runtime drift |

The ServiceAccount and ClusterRoleBinding share the same creation second, and
the Deployment followed immediately. That timing is consistent with one
initial installation operation, but creator identity cannot be proved because
`managedFields` and attributable audit records are unavailable. No Helm owner
metadata exists. Repository scripts, current documentation, declarative backup
sources, and reachable history contain no recreation source for the binding.
Therefore deleting it is not expected to be reconciled automatically, but
that remains an inference rather than a guarantee about external automation.

Git first versioned Portainer later in commit `fd08b74`; it captured the
ServiceAccount, PVC, Service, and Deployment, but not the authority binding.
The only workload drift remains the previously documented registry-prefix
normalization; the effective image digest matches Git.

## Available authority

Every targeted check below returned `yes` for
`system:serviceaccount:apps:portainer` because the binding grants the built-in
`cluster-admin` ClusterRole.

| Capability | Effective permission |
|---|---|
| Namespaced resources | Read, create, patch, update, delete across namespaces |
| Cluster-scoped resources | Read and write |
| Secrets | Get/create and cluster-wide list |
| Pod diagnostics | Logs, exec, attach, and port-forward |
| ServiceAccount tokens | Create `serviceaccounts/token` |
| RBAC | Read/write Roles, RoleBindings, ClusterRoles, and ClusterRoleBindings |
| Privilege delegation | `bind` and `escalate` |
| Identity delegation | Impersonate users |
| Namespaces and nodes | Read/write, including namespace create/delete and node patch |
| Storage | Read/write PVs and StorageClasses |
| Extension plane | Read/write CRDs and admission webhooks |

This is capability available to the Pod identity. It is not evidence that the
Portainer UI exposed or exercised every operation.

## Functional capability versus demonstrated use

Portainer's official documentation describes Kubernetes application listing,
creation and editing, deletion, scaling, logs, console, ConfigMaps, Secrets,
namespaces, nodes, storage, manifests, stacks, and Helm applications. It also
documents separate read-only, operator, user, and administrator mappings. See
[Kubernetes roles and bindings](https://docs.portainer.io/sts/advanced/kubernetes-roles-and-bindings),
[inspect an application](https://docs.portainer.io/sts/user/kubernetes/applications/inspect),
and [add an application](https://docs.portainer.io/sts/user/kubernetes/applications/add).

| Function | Technically available now | Evidence of actual use |
|---|---|---|
| View workloads, namespaces, nodes, events and storage | Yes | Installation is healthy and connected; exact viewed resources are not auditable |
| Read logs | Yes | No attributable Kubernetes audit evidence |
| Create/edit/delete or scale workloads | Yes | Not demonstrated |
| Console/exec, attach, port-forward | Yes | Not demonstrated |
| Read or manage Secrets and ConfigMaps | Yes | Not demonstrated |
| Create/delete namespaces | Yes | Not demonstrated |
| Modify RBAC, bind roles, escalate or impersonate | Yes | Not demonstrated |
| Manage nodes, PVs, StorageClasses, CRDs or webhooks | Yes | Not demonstrated |
| Deploy manifests, applications, stacks or Helm charts | Technically supported | Not demonstrated |

No non-Portainer object was safely attributable to Portainer by retained
manager metadata, labels, annotations, events, Git history, or documentation.
The recent sanitized log sample contained zero warning and error records but
cannot establish historical workflows. There is insufficient evidence to say
that Portainer has been an operator, administrator, or viewer only.

## Exposure and compensating controls

- The public HTTPRoute attaches to HTTP and HTTPS Gateway listeners and has no
  ForwardAuth filter. Portainer is not protected by Authelia; no Authelia
  policy is therefore applied to this route. Anonymous HTTPS reaches the
  native Portainer surface with HTTP 200.
- TLS terminates at the Gateway. Certificate verification from the authorized
  control-plane client did not establish trust, so certificate-chain trust is
  a separate limitation; no certificate data was printed.
- The plain-HTTP listener returned 400 rather than an HTTPS redirect, matching
  the existing `NET-002` finding.
- The Service is ClusterIP only. It has no NodePort, LoadBalancer address, or
  external IP. It exposes application port 80 and the Portainer edge port
  internally; the HTTPRoute references only port 80.
- No NetworkPolicy exists in `apps`.
- The Pod uses its dedicated ServiceAccount with a projected API token. Pod
  and container security contexts are empty, so root execution, capability
  retention, privilege escalation, and writable root filesystem are not
  explicitly constrained. It does not use host network, PID, IPC, hostPath,
  devices, or privileged mode.
- A single replica uses Recreate and mounts the RWX `portainer-data` PVC at
  `/data`. The audit did not inspect that data. Startup, readiness, and
  liveness probes are present.
- Declared and effective images resolve to the same immutable digest; only the
  known registry-prefix presentation differs.

Native Portainer authentication is a control, but the public administrative
surface, unrestricted Pod identity, absent NetworkPolicy, projected token, and
implicit container security context make compromise impact cluster-wide.

## Candidate profiles

### Profile A — Secret-free viewer (provisional recommendation)

- **Preserves:** listing and inspection of ordinary workload resources,
  namespaces, nodes, Services, endpoints, events, PVC/PV and StorageClass
  metadata, workload status, and `pods/log` where approved.
- **Removes:** all writes, Secret reads, exec/attach/port-forward, RBAC,
  impersonation, token creation, node mutation, storage mutation, CRD and
  webhook mutation.
- **Rules:** cluster-scoped `get/list/watch` only for namespaces, nodes,
  StorageClasses and PV metadata; namespaced `get/list/watch` for workload and
  operational resources; `get/list/watch` on `pods/log`; explicitly omit
  Secrets and sensitive subresources.
- **Risk/maintenance:** lowest compromise impact and small static policy, but
  the CE UI may show denied actions and exact compatibility is unproved.
- **Positive validation:** environment loads; namespaces, workloads, status,
  events, storage metadata and logs render for approved scope.
- **Negative validation:** Secret get/list, all create/update/patch/delete,
  exec/attach/port-forward, token creation, RBAC writes, bind, escalate,
  impersonate, node/PV/StorageClass mutation, CRD and webhook mutation are
  denied.
- **Rollback/downtime:** restore the reviewed prior binding. No Pod restart;
  Portainer management functions may be unavailable during validation.
- **Difficulty:** medium because CE behavior under reduced Kubernetes RBAC
  must be tested without relying on Business Edition UI restrictions.

### Profile B — Namespace-scoped limited operator

- **Preserves:** Profile A plus scale, rollout and patch of Deployments,
  StatefulSets, and DaemonSets in explicitly approved namespaces; ConfigMap
  management; logs. Exec is omitted unless a named workflow proves it
  necessary.
- **Removes:** global RBAC, bind, escalate, impersonate, token issuance, global
  Secrets, node administration, cluster storage administration, CRD/webhook
  writes, namespace deletion, and unrestricted cluster-wide mutation.
- **Rules:** a small cluster reader plus one Role/RoleBinding per authorized
  namespace for workload and scale subresources. Add individual create/delete
  verbs only after a specific workflow is approved.
- **Risk/maintenance:** compromise can mutate approved workloads; per-namespace
  bindings require maintenance. CE may not map every UI action cleanly.
- **Positive validation:** approved scale, rollout and edit scenarios plus
  Profile A tests; optional exec only if explicitly chosen.
- **Negative validation:** writes outside approved namespaces and every removed
  high-risk permission are denied.
- **Rollback/downtime:** restore the prior binding. No Pod restart; partial
  administrative outage is possible.
- **Difficulty:** high because the owner must define namespaces and exact
  operations, and Portainer CE provides fewer internal access restrictions.

### Profile C — Full administrator

- **Preserves:** current end-to-end Portainer management, including every
  Kubernetes API capability available through `cluster-admin`.
- **Rules:** the current built-in `cluster-admin` binding, but versioned and
  reviewed; it cannot honestly be described as least privilege.
- **Risk/maintenance:** maximum blast radius. Native authentication and TLS are
  insufficient compensations for a public workload with a mounted unrestricted
  cluster credential. Meaningful compensation would require stronger edge
  protection, network restriction, auditable access, hardened Pod execution,
  and preferably a separate administrative identity disabled by default.
- **Validation:** all intended administration workflows plus authentication,
  authorization and audit controls; negative Kubernetes checks are impossible
  while the identity remains `cluster-admin`.
- **Rollback/downtime:** restore the prior binding if a replacement identity
  fails. No Pod restart expected.
- **Difficulty:** low to retain, high to justify and secure adequately.

## Recommendation and staged migration

Choose Profile A provisionally because it preserves the only safe function
that can presently be supported by evidence—inspection—while removing powers
whose use is not demonstrated. Do not enforce it until the Platform owner
answers one minimum question: **must Portainer perform any mutation, and if so,
which exact verbs on which resource kinds in which namespaces, including
whether logs or exec are required?**

The later migration should be one reversible IAM-001 change:

1. Version a dedicated viewer ClusterRole/Binding while retaining the old
   binding temporarily; do not restart Portainer.
2. Validate all approved positive workflows and the complete negative matrix.
   Because both bindings are additive, use impersonated `can-i` against a
   temporary test identity bound only to the candidate role, or another
   reviewed isolation method; testing the existing SA before removal would be
   masked by `cluster-admin`.
3. Remove only the unversioned global binding after owner acceptance.
4. Observe Portainer, Kubernetes authorization failures, routes and cluster
   health for a defined window.
5. Immediately restore the exact prior binding if an approved function fails.

Profile B should replace A only after the owner supplies that action matrix.
Profile C should be retained only by an explicit risk-acceptance decision and
should use a separate normally-disabled administrative identity if feasible.
No profile is implemented by this report.

## Exact next step

Obtain the Platform owner's minimal action/namespace decision. Then prepare a
separate, reviewable IAM-001 RBAC manifest and validation plan for Profile A or
B. Do not remove the current binding, authenticate to Portainer, or modify the
workload as part of that design review.
