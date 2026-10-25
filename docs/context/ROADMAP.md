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

# Prioridades del bloque local — 23-10-2026

Código preparado, aceptación operacional pendiente: CI completo; pruebas CNI y
rollout por namespace; adopción Terraform con imports; provisión/restauración
offsite; revisión pública y limpieza decidida por el propietario. Las fases de
código no cierran los riesgos de producción. Véase baseline de octubre.

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
| Restic node-02/node-03 measured sizes | `pending` | Replace constant sizes with validated measurements in a separate authorized block; neither node changed during node-01 closure. |
| Restic historical scope validator | `pending` | Adapt the fixed checkpoint allowlist before using the historical finalizer to approve newer packages; no execution authorized in node-01 closure. |
| Off-site backup copy | `pending` | The encrypted node-03 recovery copy is independent of the NAS but remains local. Add and validate a separately governed off-site copy without weakening encryption, external password custody, exclusions or the 25 GiB guard. |
| NAS mdraid local monitoring | `completed` | Versioned systemd drop-ins add syslog delivery without modifying the array. The permanent monitor is active; the oneshot preserves its vendor `AUTOSCAN` environment and conditional execution and completes successfully. External critical delivery through Alertmanager is now completed separately. |

## Medium priority

| Work | Status | Closure criteria |
|---|---|---|
| Pin mutable direct images: Authelia (Home/Filebrowser already pinned) | `pending` | One service per commit; pin the exact running imageID without upgrading; validate routes, auth, storage, consumers, and drift zero. |
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
| Restic node-01 package freshness | `completed` | Deployed and validated 2026-09-23: fixed 30 August reference removed; newest package validated with maximum RPO 24 hours; measured 167,611,546 bytes, package age 63,113 seconds, controlled success in 17 seconds. Installed hashes match prepared files; timer waiting, service success, nine Prometheus metrics matched and no Restic firing alert. Execution success and data freshness are separate; root-only rollback retained. Manual commit/push pending. |
| Encrypted node-03 recovery copy | `completed` | Six encrypted hostname/type snapshot categories passed Restic check, scope/exclusion validation and the 25 GiB guard. Four persistent timers are enabled, active and waiting; maintenance is dry-run-only. Three-node metrics, two rules and controlled Telegram FIRING/RESOLVED passed. The copy is independent of the NAS but not offsite. |
| Raspberry Pi external monitor phase 1 | `completed` | One lightweight ARMv7 container checks representative external DNS/HTTPS/TLS/status/latency and restricted RP3 host signals with persistent three-failure alert state and independent Git-free Telegram credentials. HTTP and host-root false positives are resolved. The monitor is healthy with zero restarts; `rp3-local` intentionally remains firing for real current/historical undervoltage and throttling `0x50005` pending a 5.1 V / 2.5 A supply and short low-resistance micro-USB cable, followed later by a controlled reboot. |
| Alertmanager Telegram critical delivery | `completed` | The locked monitoring release references and mounts an external Git-free Secret. Critical firing and resolved delivery passed with a real synthetic alert; Watchdog, warning and unmatched alerts remain on `null`. The reusable interactive script supports creation and rotation without exposing credentials. |
| Traefik Gateway Shim warning correction | `completed` | Reconciled the user-supplied Helm values to the live release and removed only the obsolete issuer annotation. The manual Certificate remained Ready at revision 6, Traefik stayed 2/2, Gateway status and HTTPS consumers passed, and the warning did not recur. |
| Kubernetes backup and recovery automation | `completed` | Versioned automation and successful controlled Nextcloud restore test; `b5b8792`. |
| Kubernetes database recovery validation | `completed` | Package `20260830-031918` restored MariaDB, PostgreSQL and Redis with production digests in a default-deny temporary namespace. Aggregate structure and synthetic probes passed with measured RTOs; guarded cleanup left no namespace, PVC, Secret or Released PV. |
| Filebrowser image pinning (`IMG-003`) | `completed` | Pinned the exact effective digest only; validated route, native authentication path, storage mounts, consumer health and drift zero in the 2026-08-19 rollout. |
| Home image pinning (`IMG-001`) | `completed` | Pinned the exact effective digest only; validated two replicas, route/auth response, ConfigMap metadata, mounted files, consumer health and controller drift zero in the 2026-08-19 rollout. |
| Scrutiny cold-bootstrap recovery prerequisite | `completed` | Manual mode-0700 NAS copy from stopped InfluxDB/SQLite state, atomic publication, checksums, offline integrity validation and isolated Scrutiny 0.8.2/InfluxDB 2.2.0 startup passed on 2026-08-21. The server interruption was 83 seconds and all temporary resources were removed. This does not complete recurring RPO-24-hour backup or `SEC-003`. |
| Scrutiny backup authorization bootstrap | `completed` | Official offline InfluxDB 2.2.0 operator recovery created one dedicated runtime authorization and stored only its token and ID in `monitoring/scrutiny-backup-influx-operator` through a closed stdin pipeline. Authentication, workload health, cleanup and drift passed; no recurring backup or `SEC-003` change was made. |
| Scrutiny recurring logical backup prerequisite | `completed` | Daily official InfluxDB backup plus transactional SQLite backup publish atomically to protected NAS storage with checksums, locks and 7/8/12/5 GFS. A manual backup and full isolated restore passed on 2026-08-22; the bootstrap copy was preserved and `SEC-003` remains pending. |
| Scrutiny Hub/Spoke migration (`SEC-003`) | `completed` | Web/API has no privilege, devices, udev, hostPort, Influx tree or ServiceAccount token. Three Kubernetes collectors plus NAS cover 11 active unique devices while one July record remains historical. |
| NAS Scrutiny collector digest pinning | `completed` | Replaced only the mutable v0.8.2 collector reference with its already-running digest. The NAS collector retained its runtime contract, completed five reads and publications, and remained disjoint from the six active Kubernetes devices. No Kubernetes, privilege, mount, schedule or native-service change was made. |
| NAS Scrutiny collector endpoint recovery | `completed` | Replaced the retired host endpoint with the existing HTTPS route to `monitoring/scrutiny`, added a reproducible Compose declaration and SSH deploy workflow, and refreshed the same five identities without duplicates or send errors. |
| Actionable NAS, node and storage monitoring | `completed` | Private digest-pinned NAS node-exporter and atomic summaries feed 13 tested CHOMS rules. Target UP, timer reboot-persistent, synthetic critical FIRING/RESOLVED received, no unexpected alert, and existing warning/info routing unchanged. |
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

## Prioridad de recuperación offline — 24-10-2026

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
