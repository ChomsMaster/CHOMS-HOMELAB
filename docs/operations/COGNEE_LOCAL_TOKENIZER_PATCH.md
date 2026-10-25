# Cognee 1.6.5: tokenizer local explícito (imagen lista, importación pendiente)

## Estado al preparar el parche (histórico; actualización al final)

Parche preparado y diez regresiones offline PASS; imagen nueva **no construida**.
API continúa a cero. No se aplicó HUGGINGFACE_TOKENIZER al Deployment actual:
la imagen existente no propaga ese valor a FastEmbed. No hubo rollout ni ingesta.

## Causa demostrada

En la fuente oficial fijada al commit `37f788bd287750e10d7610173e5332b3843f6ebd`:

1. `EmbeddingConfig.huggingface_tokenizer` lee HUGGINGFACE_TOKENIZER y
   `get_embedding_engine()` la entrega a `create_embedding_engine()`.
2. La rama FastEmbed de `create_embedding_engine()` no la pasa al constructor.
3. `FastembedEmbeddingEngine.get_tokenizer()` tampoco la transmite al resolver.
4. La rama FastEmbed de `resolve_embedding_tokenizer()` ignora incluso un
   argumento explícito; resuelve el identificador remoto a través del Hub.
5. `_load()` solicita `tokenizer.json` y `_declared_input_limit()` solicita
   `tokenizer_config.json` mediante `hf_hub_download`. El fallback termina en
   `TikTokenTokenizer` → `tiktoken.get_encoding("cl100k_base")` → HTTP del BPE.

URLs observadas, sin query ni credenciales:

- `https://huggingface.co/BAAI/bge-small-en-v1.5/resolve/main/tokenizer.json`
- `https://huggingface.co/BAAI/bge-small-en-v1.5/resolve/main/tokenizer_config.json`
- `https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken`

La reproducción original, con snapshot existente y override local explícito,
falló con código 1 y una conexión bloqueada. No basta con añadir la variable.
La causa concreta de diferencias de caché entre health y add no quedó aislada;
el parche establece una ruta local estricta y elimina esa dependencia del Hub.

## Diff mínimo

[Parche](../../stacks/kubernetes/choms-memory/patches/cognee-1.6.5-local-tokenizer.patch)
y [proveniencia](../../stacks/kubernetes/choms-memory/patches/local-tokenizer-patch.json).

- Factory: propagar el argumento al constructor FastEmbed.
- Engine: conservar el argumento y entregarlo al resolver.
- Resolver FastEmbed: si hay override, exigir ruta absoluta y cargar directamente;
  errores se propagan, sin fallback Hub/TikToken en ese perfil.
- Adaptador: validar directorio/metadata sin symlinks, cargar con
  `AutoTokenizer.from_pretrained(..., local_files_only=True, trust_remote_code=False)`
  y leer el límite desde tokenizer_config.json local.

FastEmbed conserva el cálculo de embeddings. No se cambia el modelo ni se
reconstruye la caché. La ruta propuesta, solo tras construir/admitir otra imagen:

```text
HUGGINGFACE_TOKENIZER=/cognee-storage/models-76fb6636f317812a/hub/models--BAAI--bge-small-en-v1.5/snapshots/5c38ec7c405ec4b44b94cc5a9bb96e735b38267a
```

## Pruebas y reproducción

[Test](../../scripts/memory/test_local_tokenizer_patch.py): diez casos, sin pesos
ni bases de datos. La propagación de factory/constructor se verifica por AST;
el resolver y get_tokenizer se ejercitan realmente sobre el snapshot local.
No se afirma una validación completa de cognee.add sobre una imagen nueva.

Aplicar el parche únicamente a una copia desechable de la fuente verificada,
antes de cualquier instalación frozen futura. La prueba realizada usó la imagen
actual sin modificarla, cuatro mounts read-only explícitos sobre los archivos
parcheados y el snapshot BAAI read-only en la ruta anterior. Docker network=none,
UID 1000, guardas de auditoría de sockets, variables offline existentes y mapa
LiteLLM local. No hay monkeypatch de funciones ni sitecustomize.

Invocación dentro de ese harness, con mounts explícitos ya preparados:

```bash
python /regression.py -v
```

No ejecutar el test con el Python global ni activar el parche mediante mounts
en producción. Es necesaria una imagen nueva con digest propio y admisión
separada; no reutilizar el tag de la imagen ya importada.

## Dataset y continuación posterior

Consulta READ ONLY: un dataset exacto `choms-homelab-public`, cero filas de
`data`. Esto no acredita ausencia de fragmentos vectoriales o de grafo.
No se borró nada. Antes de otra ingesta, eliminar únicamente ese dataset mediante
la API soportada de Cognee y verificar fragmentos; nunca limpiar PostgreSQL o
volúmenes de forma general. Después corresponden rollout, 401/200, ingesta
sintética pequeña, corpus público, consulta trazable, persistencia y restore.
MCP y OpenHands siguen bloqueados; sin build, commit o push en este bloque.


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
