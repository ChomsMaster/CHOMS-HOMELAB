## Cognee — estado de cierre 25-10-2026

- `completed`: API privada, ingesta 36/36, consulta trazable y persistencia tras
  restart API; RAM 8/16 GiB, máximo observado 12,20 GiB, cero OOM/reinicios.
- `blocked`: MCP; el candidato no demuestra autenticación entrante ni
  compatibilidad con API 1.6.5. No desplegarlo por tener solo un digest fijado.
- `pending`: backup/restore en bloque separado; actualización incremental del
  corpus después de aprobar el diff. No afirmar RPO/RTO ni recuperación real.
- `deferred`: OpenHands y los demás agentes fuera del alcance autorizado.
- Cambios locales preparados, sin commit ni push. Historial previo conservado.

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
