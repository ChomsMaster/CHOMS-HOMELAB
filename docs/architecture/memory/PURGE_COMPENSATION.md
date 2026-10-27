# Gate de purga lógica de choms-memory

## Resultado y alcance

Gate sintético completo PASS (27-10-2026): escritura canónica, lectura, búsqueda
con FastEmbed local, borrado, reinicio del contenedor y ausencia de resurrección.
[Recibo saneado](purge-e2e.json). No se usaron datasets existentes, memorias reales,
LLM generativo, proveedores, backups ni configuraciones MCP de clientes.

Esto incorpora la compensación reutilizable y su gate, **no un MCP productivo**.
El servidor `gate_adapter.py` solo admite dos textos artificiales y el proyecto
`choms-memory-e2e-test`. No cumple todavía el contrato completo de ocho tools de
la gobernanza y no se registra en Codex/Hermes. La persistencia real sigue cerrada.

## Defecto y procedencia

Cognee 1.6.5 importa el handler efectivo desde `/src/cognee`; su SHA-256 coincide
con la copia instalada. `LadybugDatasetDatabaseHandler.delete_dataset` evacua
la caché y elimina main, `.lock` y `.wal`, pero omite `.shadow` y otros companions.
La reproducción llama al handler instalado sin extraer/reemplazar su AST:
quedó solamente `.shadow`; el wrapper eliminó ese resto y la segunda ejecución
terminó correctamente. No se modifica el handler global.

Ladybug Python y motor nativo: 0.19.0. Fuente oficial
[LadybugDB/ladybug v0.19.0](https://github.com/LadybugDB/ladybug/tree/c934f673b6b1c5b680bdae3295cbd909b5855cef).
El [lock](../../../tools/choms-memory/purge-contract.json) fija commit, hashes
nativo/handler y fuentes. El binario instalado contiene los nombres de locks de
checkpoint y `wal.checkpoint`; la versión efectiva procede de `Database.get_version`.

Allowlist exacta para `<UUID>.pkl`:

| Artefacto | Evidencia |
| --- | --- |
| main | handler `create_dataset`, alias de proveedor `kuzu` |
| `.wal`, `.shadow`, `.tmp`, `.wal.checkpoint` | `StorageConstants`, `StorageUtils` |
| `.checkpoint.intent.lock`, `.checkpoint.apply.lock` | `StorageUtils`, `Checkpointer` |
| `.lock` | handler oficial; allowlist de `LocalFileSystem` |

`DatabaseManager` admite archivos de subgrafos con nombres adicionales. Este
perfil **no permite subgrafos, tablas externas ni objetos no registrados**:
cualquier entrada adicional en el directorio exclusivo bloquea la purga antes
del handler. No se utiliza la regla amplia por prefijo de `LocalFileSystem`.
La lista no se anuncia como universal para otras versiones/proveedores.

## Barrera, almacenamiento y reconciliación

PostgreSQL existente, rol y esquema nuevos exclusivos de prueba. El handler
oficial `pgvector_shared` crea/elimina esquemas por dataset en esa misma base;
no se crea otra base. El grafo tiene raíz propia en `emptyDir`, montada solo por
el gate. Los modelos existentes se montan únicamente read-only por subPath.
Cada memoria tiene UUID de dataset y propietario generados internamente: ningún
nombre, ruta ni flag de exclusividad procede de una petición del usuario.

Un advisory lock de sesión PostgreSQL cerca todos los escritores/proyecciones.
Se confirma `purge_pending`, retirando cuerpo y hash canónicos, antes de efectos
externos. Se cierran conexiones nativas antes del handler y se usa la evacuación
oficial de sus cachés; no se abre el grafo para borrarlo. La compensación:

1. Recorre raíz y directorio con `O_DIRECTORY|O_NOFOLLOW`; exige UID propio y 0700.
2. Usa `lstat` equivalente (`follow_symlinks=False`) y allowlist cerrada. Rechaza
   symlinks, hardlinks, traversal, dispositivos, directorios y archivos inesperados.
3. Ejecuta primero el handler oficial y comprueba estabilidad del directorio y
   de cada resto (dev/inode/tamaño/mtime/ctime), sin exigir atime estable.
4. Elimina solo los restos autorizados, sincroniza directorios y verifica vacío.
5. Elimina el esquema vectorial mediante el handler oficial, invalida caché propia
   y exige postcondiciones antes de confirmar la tombstone y retirar el registro.

Cualquier fallo conserva `purge_pending` sin contenido; el arranque reconcilia
únicamente registros internos pendientes bajo el mismo lock. Una tombstone final
contiene solo `id` opaco y `state=forgotten`. No conserva resumen, hash de contenido,
embedding, nombres o referencias. Quedan permitidos directorios UUID vacíos,
no archivos. La raíz es privada: no se garantiza seguridad ante un actor root o
un proceso malicioso con el mismo UID que pueda cambiarla fuera de la barrera.

## Prueba y operación

27 pruebas offline cubren cada suffix, fallos/cortes, reintento, permisos, enlaces,
tipos, directorio sustituido, raíz/traversal, exclusividad y postcondición.
El gate live autentica solicitudes (401 sin token), usa embeddings reales locales
y PostgreSQL/pgvector/Ladybug reales. Antes de borrar existe un nodo y un embedding.
Después: cero filas canónicas, esquema vectorial ausente, cero archivos de grafo,
cero caché y una tombstone. No se reabre un grafo eliminado para contarlo, pues
eso recrearía el archivo: la ausencia de todos los artefactos, con handles cerrados,
acredita ausencia de sus nodos y aristas persistidos. Búsqueda/lectura siguen vacías
tras reiniciar el proceso. `emptyDir` se conserva en ese reinicio del contenedor;
esto no acredita recuperación tras pérdida de nodo ni persistencia productiva.

Reejecución exclusivamente sintética y autorizada:

```bash
python3 scripts/memory/memory_purge_e2e.py --execute-synthetic --ssh-target USER@CONTROL_PLANE
```

El runner crea objetos nuevos con nombres aleatorios, rol/esquemas aislados,
ConfigMap inmutable, Secret efímero, ClusterIP, políticas default-deny y permisos
mínimos hacia PostgreSQL/DNS. Dry-run servidor y diff preceden al apply. No root,
ServiceAccount token, ruta pública o pull remoto. Reutiliza la imagen local
bloqueada y comprueba que su imageID coincide con la instancia Cognee aceptada;
no confunde digest de índice OCI con imageID de CRI. El gate elimina sus recursos,
rol y esquemas al terminar. No borra datos, PVC, Secrets o datasets existentes.

El desarrollo del gate corrigió importación circular por orden incorrecto,
`DB_PORT` ausente y SIGTERM ignorado por Python como PID 1. El reinicio demostrado
usa SIGINT; estos fallos eran del harness, no pruebas de un defecto de Cognee.

## Garantías, límites y rollback

Es **borrado lógico completo del estado online aislado**, no sobrescritura física
de bloques. No elimina WAL de PostgreSQL, snapshots, backups, réplicas offline ni
copias externas. Su tratamiento requiere otra política explícita; nunca se
promete olvido físico o eliminación de backups con esta operación.

El gate queda desmontado; rollback de este bloque es revertir su commit, sin
operaciones live. No activar escrituras reales ni restaurar automáticamente un
`purge_pending`. Si aparece un artefacto desconocido, mantener pendiente e
investigar su versión/propiedad; no ampliar la allowlist por prefijo.

Pendiente: conectar esta compensación al MCP productivo con esquema completo de
gobernanza, autorización por ámbito, CAS y ocho operaciones; volver a acreditar
su E2E antes de registrar clientes o aceptar la primera memoria real.
