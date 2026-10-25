# Cognee API — ingesta y persistencia verificadas; MCP no admitido

Estado actual 25-10-2026: API y PostgreSQL Ready en node-02, solo ClusterIP;
request/limit 8/16 GiB. Ingesta 36/36, consulta y restart/persistencia PASS;
pico cgroup 12,20 GiB, cero OOM y cero reinicios. Grafo: 2.226 nodos y
6.040 aristas. MCP no desplegado; backup/restore pendiente en bloque separado.
La operación y las restricciones se detallan en el cierre al final de
[este runbook](../../../docs/operations/MEMORY_PLATFORM.md).

## Histórico de preparación (sustituido por el cierre actual)

# Cognee — tag local resuelto; validación imageID detenida

Namespace: `choms-memory`. PostgreSQL y recursos base aplicados; credenciales
solo runtime. API y MCP no aplicados. Véase la corrección al final. Los pins consultados están en
[release-lock](../../../docs/architecture/memory/release-lock.json).

API estable: v1.6.5; el release más reciente es v1.6.6rc1. Se descartaron rc/dev
como base inicial. La imagen API 1.6.5 existe y su digest está verificado; el tag
oficial MCP 1.6.5 devuelve 404. El candidato MCP `main-37f788b` tiene digest
inmutable, pero no se supone compatible con API 1.6.5 ni autenticado en entrada.
El token `COGNEE_API_KEY` del CLI MCP autentica contra la API de salida: no
acredita que el endpoint MCP HTTP exija autenticación. Es un gate independiente.

El ejemplo oficial `examples/guides/no_llm_remember_recall.py` de v1.6.5 permite
GLiNER demo + FastEmbed locales, `AUTO_FEEDBACK=false` y búsqueda CHUNKS sin
LLM. Los tipos *_COMPLETION requieren LLM y quedan prohibidos. Embeddings y NER
son inferencia local autorizada. FastEmbed pasó el fixture offline; GLiNER
falló en la carga del tokenizer. No hubo ingesta ni consulta real.

Contrato de despliegue tras resolver los gates:

- API y MCP con autenticación entrante obligatoria y versiones compatibles,
  PostgreSQL + pgvector; cero claves/fallback de proveedores.
- `TELEMETRY_DISABLED=true`, extractor GLiNER local, embeddings FastEmbed,
  sin feedback/síntesis generativa. Modelos y dependencias precargados y fijados
  fuera del runtime: descargar modelos no justifica egress público permanente.
- Services únicamente ClusterIP, sin rutas públicas. SSH por el control plane;
  origen CNI autorizado /32 cuando corresponda al recorrido demostrado.
- Default-deny; solo DNS a CoreDNS, Cognee hacia PostgreSQL y entradas mínimas
  desde OpenHands/SSH. No usar `0.0.0.0/0` para descargar modelos en ejecución.
- Nodo seleccionado preliminar: choms-node-02 por margen de RAM y disco, sin
  trasladar otros servicios. StorageClass dedicada Retain/WaitForFirstConsumer,
  PVC y afinidad local; sin usar la clase OmniRoute para otro servicio.
- Recursos, probes, ausencia de host namespaces/privilegios, SA sin token automático.
  Monorréplica: no presentar un PDB minAvailable=1 como alta disponibilidad.
- Dataset `choms-homelab-public`, solo corpus aprobado, metadatos Git actuales,
  commits y documentación pública; ninguna transcripción o repositorio privado.
- Importación incremental con identidad estable/hash de documento y dataset
  explícito. Dos datasets sintéticos deben demostrar aislamiento real.
- Aceptación: «¿Cómo se resolvieron los bloqueos de OmniRoute?» mediante CHUNKS
  con referencias verificables a archivos y commit c1af248. No atribuir a un
  LLM una respuesta que no se generó.

Los manifiestos preparados fijan imágenes por digest y credenciales mediante
referencias a Secrets runtime todavía inexistentes. No se deben aplicar hasta
resolver el gate offline, hacer dry-run/diff servidor y validar autenticación.
No se necesitan rollback ni borrado: el componente no se aplicó.
El procedimiento de backup/restore debe pasar antes de su aceptación; véase
[operación](../../../docs/operations/MEMORY_PLATFORM.md).


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
