# CHOMS Memory v1 — operación interna

Estado 27-10-2026: MCP independiente operativo y validado con fixtures desde Codex
CLI y Hermes nativos, sin inferencias. Memorias reales y captura automática OFF.
Codebase Memory conserva su función de índice de código y su allowlist anterior.

## CHOMS Memory — intento de captura en node-01, 2026-10-30

Lectura de systemd: el servicio instalado ejecuta `--scheduled-capture`, inició a
las 07:15:00 CET y terminó a las 07:16:14 CET con `ExecMainStatus=1`. Fue un
intento de backup; no hay evidencia de restore ni de backup completo. El timer
figura ahora `disabled/inactive`, sin última ni próxima activación registrada.
La coincidencia horaria no prueba que el timer iniciara el servicio. No se
recuperó la etapa del fallo ni se consultaron snapshots/marker; el journal de la
invocación requiere sudo interactivo. No se repitió ninguna operación ni se
modificó el servicio, el timer o los datos. Memorias reales y captura automática
no se habilitaron; los gates no se revalidaron en esta consulta.


## Arquitectura y contrato real

Endpoint del Service `choms-memory.choms-memory.svc.cluster.local:8080/mcp`.
Los agentes utilizan stdio JSON Lines → SSH estricto al control plane → kubectl
exec → puente HTTP loopback autenticado. No listener local persistente, túnel,
Ingress, HTTPRoute, NodePort, LoadBalancer, DNS ni TLS público nuevo. La
NetworkPolicy no admite ingreso de otros Pods; el puente opera dentro del Pod.
El acceso operativo requiere SSH/kubectl autorizado existente; no instala RBAC
privilegiado en el contenedor y no amplía permisos del operador.

Exactamente ocho herramientas: `health`, `propose`, `remember`, `search`, `review`,
`supersede`, `forget`, `checkpoint`. Esquemas ejecutables en
[contract.py](../../tools/choms-memory/contract.py), flujo y fixtures en
[memory_mcp_e2e.py](../../scripts/memory/memory_mcp_e2e.py).

Fuente canónica: PostgreSQL existente, DB cognee, esquema choms_memory y rol
choms_memory_adapter independiente (sin superuser/CREATEDB/CREATEROLE). CREATE
sobre la DB es necesario para pgvector_shared; no es aislamiento adversarial
entre tenants. Scopes global/personal/project son particiones de un propietario.
Proyección: esquema pgvector_shared y unidad Ladybug privada por UUID interno,
exclusivos del adaptador; nunca datasets ni handler global de Cognee alterados.
FastEmbed local genera vectores; no LLM, proveedores, OmniRoute ni red automática.

Autenticación fail-closed: credenciales aleatorias independientes por cliente y
contraseña del rol en Secret runtime choms-memory-runtime, no OAuth. Se generan
en memoria en node-01 y nunca viajan en configuración de agentes, Git ni logs.
El proceso stdio dentro del Pod lee solo el token de su cliente. El operador con
kubectl exec conserva acceso privilegiado operativo; no es una frontera multiusuario.
Readiness solo comunica disponibilidad; /metrics exige autenticación y etiqueta
únicamente operación/resultado. Logs de fallo: clase, errno/sqlstate y línea técnica,
sin mensajes SQL, argumentos, memorias, IDs de proyecto ni valores de credenciales.

## Despliegue y migración

[central.yaml](../../stacks/kubernetes/choms-memory/central.yaml) fija node-02,
250m/1Gi request, 1 CPU/3Gi limit, UID/GID1000, rootfs read-only, RuntimeDefault,
capabilities vacías y SA propio sin token. Solo /state (PVC propio) y /tmp son
escribibles; modelos existentes se montan read-only. PVC choms-memory-state:
local Retain, WaitForFirstConsumer, afinidad node-02. No se recreó PostgreSQL.

Se reutiliza la imagen ya importada: pin por ID de configuración CRI sha256,
imagePullPolicy Never. [runtime.lock.json](../../tools/choms-memory/runtime.lock.json)
registra índice OCI, manifiesto amd64, configuración y imageID efectivo. Son
identificadores distintos: no se exige igualdad textual entre índice y imageID.
La asociación se verificó leyendo los JSON con hashes del archivo OCI existente;
LocalResolve de containerd 2.3.2 admite el ID crudo de configuración.

Código propio empaquetado en ConfigMap inmutable con hash, generado mediante:

```bash
python3 scripts/memory/render_memory.py --check
```

El bootstrap [bootstrap.py](../../tools/choms-memory/bootstrap.py) recibe por stdin
una lista cerrada de los recursos versionados; está diseñado para ejecutarse solo
por el operador en el control plane. Genera rol/esquema/Secret únicamente si todos
están ausentes y falla ante estado parcial; nunca rota ni lee credenciales existentes.
Realiza dry-run servidor y diff acotado antes de aplicar. Revisar siempre ese diff.
La migración [001.sql](../../tools/choms-memory/migrations/001.sql) es versionada,
idempotente y comprueba versión exacta al arrancar; reconciliación de proyección
pending/purge_pending se realiza antes de servir peticiones. No hay down destructivo.

## Concurrencia, consentimiento y recuperación

CAS expected_revision y request_id UUID estable en reintentos; lock PostgreSQL y
transacciones impiden actualizaciones perdidas. supersede conserva el linaje y
solo una decisión activa por scope/proyecto/topic. El contenido normalizado deduplica;
equivalencia semántica/contradicción ambigua requiere juicio del agente. La identidad
MCP autentica al agente, no prueba criptográficamente la intención del usuario.
La skill interpreta consentimiento; source_kind web/tool/repository se rechaza.

Proyección semántica no es la fuente canónica: fallo de proyección deja pending y
error explícito; no se informa éxito ni se crea cola alternativa. Expiración cambia
estado/revisión al leer y excluye recuperaciones activas. Presupuesto predeterminado
5 registros/2400 caracteres, máximo 10/6000, critical/high; medium/low solo opt-in.

forget purga todo el linaje: borra contenido y hashes canónicos/recibos, vectores,
grafo y companions con wrapper previamente validado; caché de contenido no existe.
Solo conserva UUID/revisión/estado/IDs opacos de peticiones en tombstone. Corte o
error conserva purge_pending y se reconcilia sin anunciar forgotten prematuramente.
Allowlist Ladybug fija en [contrato de purga](../architecture/memory/PURGE_COMPENSATION.md).
Esto acredita borrado lógico operativo, no sobrescritura forense ni eliminación
física de MVCC/WAL, RAM, logs de clientes o copias históricas.

## Agentes y aceptación sintética

Codex: nueva sección mcp_servers.choms-memory en su config de usuario; Hermes:
entrada separada con tools.include exactamente las ocho operaciones y resources/
prompts false. Comando python3 -I scripts/memory/choms_memory_mcp.py, destino SSH
obligatorio y cliente enumerado. No secretos locales, OAuth ni redirección de modelos.
La entrada y allowlist de choms-codebase-memory se verificaron intactas.

Checks reproducibles sin turnos de modelo (usar el Python administrado de Hermes):

```bash
python3 scripts/memory/verify_codex_memory.py --ssh-target USER@CONTROL_PLANE --registered --discover-only
/path/to/hermes-managed-python scripts/memory/verify_hermes_memory.py --ssh-target USER@CONTROL_PLANE --registered --discover-only
```

Los verificadores sin --discover-only crean exclusivamente fixtures; --verify-only
acepta un recibo sintético anterior para probar ausencia de resurrección. No lanzar
mutaciones para una mera comprobación de descubrimiento.

E2E real de ambos clientes PASS: ocho herramientas, health, propose, aprobación
remember, read-by-ID, búsqueda semántica local, dedup, CAS obsoleto, supersede
atómico, scopes y presupuesto, checkpoint, forget del linaje, cero filas/vectores/
artefactos/caché/recibos de contenido, tombstone opaca. Reinicio con el mismo PVC:
no resurrección. Un registro activo sintético sobrevivió con búsqueda y se purgó.
Dos sesiones simultáneas: un ganador CAS y un cas_conflict. Expiración y rechazo
HTTP401 de credencial ausente/incorrecta PASS. Contador de salida automática cero.

Se eliminaron, después de acreditar las tombstones tras reinicio, los 23 registros
sintéticos y sus tombstones/directorios vacíos. El limpiador admin es solo operador,
no una novena herramienta, y falla ante contenido, trabajos o IDs desconocidos.
No se guardó «seguimos skill», chats ni datos reales.
[Evidencia sanitizada](../architecture/memory/central-e2e.json).

## Backups: gate obligatorio antes de recuerdos reales

**Cobertura completa actual: NO acreditada.** No se ejecutó ni cambió ningún backup.
El paquete Cognee manual aceptado anteriormente predató este servicio; su dump
completo de DB cognee incluiría el esquema canónico y las proyecciones vectoriales
en una ejecución futura sin exclusiones. Su captura de grafo se limita al PVC
cognee-data: no cubre choms-memory-state. No equivale a backup completo de memoria.

Lectura del script instalado node-01: selecciona paquete lógico de Kubernetes y
estado K3s, no el nuevo PVC. Su SHA difiere de la versión Git: no se presume paridad
ni exportación explícita de Secrets. El script lógico instalado coincide con Git y
selecciona bases del namespace databases, no PostgreSQL de choms-memory.
El backup node-02 declarativo captura configuración de Jellyfin, no el nuevo PVC.
Estado K3s podría retener recursos/credenciales: requiere revisión separada de
cobertura, nunca su extracción aquí. Configuración/migraciones/locks están en Git;
no hay respaldo integral automático acreditado del nuevo almacenamiento.

Semánticas separadas:

- **forget-live**: borrado lógico inmediato verificado de contenido y proyecciones
  operativas, con tombstone opaca; no significa sobrescritura física segura.
- **backup-expiry**: plazo máximo en que una copia cifrada histórica puede retener
  contenido. Actualmente **no acreditado/no acotado**: 7 diarias/4 semanales/6 mensuales
  por conteo o un forget dry-run no demuestran fecha máxima ni eliminación efectiva.

**Recomendación pendiente de aprobación, no aplicada:** backup cifrado diario propio,
retención temporal de 7 días y expiración/prune auditado al menos cada 24 horas:
objetivo máximo 8 días de recuperabilidad histórica. Sin copias mensuales/anuales
ni retención indefinida de contenido. Evitar inclusión paralela de estos esquemas
/PVC en paquetes con retención más larga antes de acreditar ese máximo. Considerar
soporte remoto/replicas y bloques físicos por separado. La tarea no autoriza cambiar
retención, ejecutar prune, borrar snapshots o afirmar borrado total.

Restore futuro debe aislar esquema/rol, vector y PVC, usar misma versión Ladybug,
reaplicar un ledger de borrado/tombstones vigente **antes de exponer** la copia y
acreditar ausencia de resurrección. Definido, no se ejecutó backup ni restore aquí.

## Primera memoria real: autorización pendiente

1. Aprobar política/coverage de backups con máximo backup-expiry conocido; tramitar
   aparte cualquier cambio de respaldos existentes. «seguimos skill» sigue pendiente.
2. Orden explícita sugerida: «Autorizo habilitar memorias reales en choms-memory
   con la política de backups aprobada [referencia/versionado]; recuerda la regla
   seguimos skill y su lista mínima como requirement/high del proyecto CHOMS».
3. Solo entonces cambiar declarativamente MEMORY_BACKUP_POLICY_ACKNOWLEDGED y
   MEMORY_ALLOW_REAL a true, conservando MEMORY_AUTOMATIC_CAPTURE=false; regenerar,
   validar/dry-run/diff/aplicar y verificar health.real_memory_allowed=true.
4. La skill realiza remember con referencia corta a esa autorización y review por ID;
   confirmar solo el recibo real. Nunca etiquetar un recuerdo real como fixture:.

## Rollback reversible

```bash
python3 scripts/memory/render_memory.py --rollback | kubectl apply --dry-run=server -f -
# Tras revisar diff y autorización operativa, quitar --dry-run=server.
```

El manifiesto generado reduce exclusivamente deployment/choms-memory a cero,
conservando PVC, Secret, rol, esquema, vectores, grafo y tombstones. No toca Cognee
ni PostgreSQL existentes. Revertir el ConfigMap hash a una revisión previa compatible
requiere comprobar migración versionada; nunca aplicar down ni borrar tablas/PVC.
La retirada de clientes elimina solo las entradas choms-memory, no otras configs.
La prueba del rollback es dry-run servidor, no una parada adicional del servicio.
