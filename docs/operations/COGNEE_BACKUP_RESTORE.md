# Cognee — backup consistente et restauración aislada

Estado: **backup y restore aislado aceptados el 26-10-2026**. Base protegida
`11d9150`. Evidencia sanitizada: [aceptación](../architecture/memory/backup-restore-acceptance.json).

## Resultado aceptado

- Backup set: `20261025T222914Z-2e9b33c6`.
- Marker snapshot: `062cfac7883306df2e5d13a92b6e8bf367dfe91049d0b184e26d9f027fceba41`.
- Restore: **36 documentos / 2.226 nodos / 6.040 aristas**, RTO **482,09 s**.
- Live Ready al terminar; recursos temporales eliminados; snapshots y staging
  OCI preservados. Confirmación del operador, sin repetir pruebas al cerrar Git.
- RPO periódico no acreditado: una ejecución no demuestra periodicidad ni
  retención efectiva. Backup local cifrado; no acredita protección offsite.

## Consistencia y fuentes

El [contrato](../architecture/memory/backup-contract.json) reúne ambas bases
PostgreSQL/pgvector, documentos admitidos, unidad fría Ladybug 0.19.0 (alias
kuzu), modelos fijados, configuración/locks/parche y OCI inmutable. El lock
asyncio de Cognee no constituye una barrera entre procesos.

La captura mutable se hizo con los escritores Cognee detenidos y sin Pods con
montajes escribibles, manteniendo PostgreSQL Ready. Se validan inode, tamaño y
mtime estables. La unidad de grafo incluye **main obligatorio y .wal/.shadow
opcionales**. No borrar, truncar, excluir WAL/shadow ni ejecutar CHECKPOINT.
Solo el restore aislado abre la unidad completa y permite recovery/replay nativo.
La reactivación live es obligatoria ante éxito, error o señal.

Los dumps custom se producen con pg_dump soportado para **dos bases distintas**:
relacional y base vectorial del dataset. Nunca copiar el filesystem PostgreSQL.
Fuentes mutables van en streaming a Restic cifrado. Cada parte requiere código
de salida correcto, tamaño y SHA-256; un snapshot parcial no acredita éxito.
El marcador COMMITTED.json se publica solo tras verificar todas las partes.
Snapshots parciales anteriores siguen ignorados y preservados, sin prune/unlock.

Única excepción de staging persistente: **OCI inmutable**, transferido con
rsync --partial --append-verify a .partial privado; tamaño/hash/índice fijados,
promoción atómica root-only y snapshot Restic del archivo local, sin stdin/SSH.
No extiende permiso de persistencia a dumps, WAL, documentos o credenciales.
No borrar todavía el OCI preservado: requiere autorización separada.

## Restore por archivo y metadatos vector

Crear namespace aislado único, sin Services/rutas públicas ni montajes live,
NetworkPolicy default-deny, SA propio sin token y credenciales temporales.
Verificar primero marcador autenticado y pertenencia de snapshots al backup set.

1. Descargar cada dump pequeño a `/run` tmpfs root-only: directorios 0700,
   archivos 0600, sin enlaces; verificar tamaño, SHA y cabecera custom PGDMP.
2. Copiar un archivo finito al tmpfs del Pod temporal, verificar allí tamaño y
   SHA, y cerrar sus descriptores. **No usar restic dump | kubectl exec -i**.
3. Precrear vector **0.8.2 como postgres** en ambas bases temporales. Examinar
   `pg_restore -l` de cada archivo; el dump relacional aceptado tiene 199 entradas.
4. Preparar una lista TOC que omita **solo `COMMENT - EXTENSION vector`** si
   existe; conservar EXTENSION, todas las demás entradas, tablas y datos.
   La entrada causaba `ERROR: must be owner of extension vector` porque el
   restore actúa como cognee. El ID numérico se obtiene del TOC, nunca se fija.
5. Ejecutar pg_restore desde archivo con `--no-owner --no-privileges
   --exit-on-error --role=cognee --use-list <lista> --dbname <base> <dump>`.
   Aplicar separadamente al dump relacional y vectorial, cada uno en su base;
   no restaurar ambos en cognee, no usar postgres como propietario de las tablas.
6. Verificar vector 0.8.2 propiedad de postgres y objetos restaurados propiedad
   de cognee. Excluir de ese último conteo miembros internos de la extensión y
   sus dependencias automáticas; public es un schema preexistente.
7. Restaurar archivos grandes mediante copias finitas verificadas al volumen
   temporal; validar el hash completo antes de extraer. Nada de plaintext en
   almacenamiento persistente. Replay Ladybug con la misma versión Cognee/Kuzu.
8. Exigir 36/2226/6040 y metadatos vectoriales equivalentes. Ante fallo capturar
   primero stdout/stderr sanitizados, estado, logs/describe clasificados y
   pg_stat_activity agregado, sin consultas, datos o credenciales; timeout por
   operación, nunca ignorar errores globalmente.
9. Cleanup de todos los recursos UID-registrados y plaintext temporal en finally;
   confirmar live Ready/intacto. No modificar PVC, Secrets, snapshots ni OCI live.

Los helpers mantenidos en [postgres_recovery.py](../../scripts/memory/postgres_recovery.py)
conservan el filtro exacto, hash del dump, argumentos por archivo y consulta de
ownership. Los launchers operativos específicos de la sesión permanecen fuera
de Git; este cierre no instala un collector, timer ni restore automático.

## Integridad, evidencia y límites

`verify_recovery.py` conserva el verificador inicial para paquetes completos
legacy `choms-cognee-recovery-v1`; **no interpreta el marker de streams v2** ni
requiere materializar el OCI completo en tmpfs para el flujo aceptado.
Integridad PASS no equivale a restore PASS. Las pruebas de corrupción/ausencia
son sintéticas; la recuperación real está acreditada por el recibo del operador.

Git conserva únicamente contratos, código, tests y recibo sanitizado: sin dumps,
modelos, tar, OCI, datasets, credenciales, logs crudos ni artefactos de /tmp.
El detalle de hashes por parte queda autenticado dentro del marcador cifrado;
no inventar ni reconstruir valores no entregados. RTO medido desde inicio del
restore hasta aceptación aislada; RPO periódico, automatización y offsite siguen
pendientes. **Listos para comenzar el bloque MCP**, con procedencia,
compatibilidad 1.6.5, autenticación entrante y handshake aún como gates propios.
