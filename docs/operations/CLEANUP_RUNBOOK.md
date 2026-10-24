# Limpieza: decidir antes de borrar

Preparado localmente a partir del inventario del 23-10-2026. **No ejecutado**.
No se ha modificado ni eliminado ningún Pod, PVC, PV, Job o directorio NAS.
Los nueve Pods Error son históricos de staging (61 días en el inventario), no
prueba de fallo actual; Moodle conserva Jobs recientes exitosos. No diagnosticar
su causa sin evidencia. Los seis PVs Released/Retain pueden contener datos útiles.

## Pods y Jobs de staging

Namespace: `colegio-maria-rosario-staging`. Candidatos exactos del inventario:

```text
colegio-moodle-checkpoint2-9kkl4
colegio-moodle-checkpoint2-retry-jf2bb
colegio-moodle-cron-29790870-4csqj
colegio-moodle-cron-29790870-7nt9g
colegio-moodle-cron-29790870-bmqsx
colegio-moodle-cron-29790870-fktk7
colegio-moodle-cron-29790870-hwm9j
colegio-moodle-cron-29790870-n2dwf
colegio-moodle-cron-29790870-pgfbh
```

Antes de autorizar limpieza, seleccionar contexto explícito y confirmar:

```bash
kubectl --context CONTEXTO -n colegio-maria-rosario-staging get pods -o wide
kubectl --context CONTEXTO -n colegio-maria-rosario-staging get pod NOMBRE_EXACTO -o jsonpath='{.metadata.uid}{"\n"}{.metadata.ownerReferences}{"\n"}{.status.phase}{"\n"}'
kubectl --context CONTEXTO -n colegio-maria-rosario-staging get job JOB_DUENO -o jsonpath='{.metadata.uid}{"\n"}{.metadata.ownerReferences}{"\n"}{.status}{"\n"}'
kubectl --context CONTEXTO -n colegio-maria-rosario-staging get cronjob colegio-moodle-cron
```

Identificar el Job dueño por ownerReference UID, y si el Job pertenece al CronJob
actual o a un checkpoint manual. Guardar solo fechas, exit codes, motivos y
evidencia agregada necesaria. No copiar logs sin saneado, dumps ni env de Pods.
Comprobar que el cron actual completa, que las DB y aplicaciones están sanas y
que no hay investigación/retención pendiente. Un Pod sin dueño se evalúa aparte.
No reejecutar Jobs viejos para demostrar que son prescindibles.

Si el propietario aprueba, eliminar **un recurso por nombre/UID revisado**, nunca
`delete pods --all`, filtros globales de Failed ni borrado de todos los Jobs.
Elegir Pod o Job de acuerdo al ownership; borrar un Job puede borrar sus Pods.
No hay rollback de un Pod/Job eliminado: por eso se conserva evidencia antes.
Verificar que no se crea un reemplazo inesperado y que el cron siguiente termina.

El manifiesto propuesto añade `successfulJobsHistoryLimit: 1`,
`failedJobsHistoryLimit: 2` y `jobTemplate.spec.ttlSecondsAfterFinished: 86400`.
TTL afecta a Jobs futuros que reciban ese spec; history limits pueden recoger
Jobs antiguos propiedad del CronJob cuando se despliegue el cambio. Esa futura
limpieza de controlador exige revisar evidencia antes del rollout. Los checkpoints
manuales sin owner del CronJob no quedan cubiertos por sus límites de historial.

## PVs Released/Retain

Todos del inventario con StorageClass `choms-nfs`, servidor `192.168.1.167` y
política Retain. No confundir Released con vacío o sin valor:

| PV | Pista de dueño en ruta NFS, no prueba |
|---|---|
| pvc-11bbb8a2-3db6-46d3-9399-06fff021610f | staging/moodle-backups |
| pvc-3ea3c782-e78c-448f-9928-a3d4c59929e7 | staging/moodle-db |
| pvc-57d81526-74b9-4b09-b387-29502769c532 | diagnóstico/mariadb |
| pvc-78f02964-0572-4324-bd43-814052e509c0 | diagnóstico/moodledata |
| pvc-cd71f493-96c6-46f5-86a8-0e5cea508bb1 | staging/moodledata |
| pvc-e6bb782e-b3d3-47d5-8bb0-1066289babe0 | diagnóstico/backup |

Consultas futuras autorizadas, sin exportar objetos sensibles:

```bash
kubectl --context CONTEXTO get pv PV_EXACTO -o jsonpath='{.metadata.uid}{"\n"}{.status.phase}{"\n"}{.spec.persistentVolumeReclaimPolicy}{"\n"}{.spec.claimRef}{"\n"}{.spec.nfs}{"\n"}{.metadata.finalizers}{"\n"}'
kubectl --context CONTEXTO get pvc -A -o custom-columns=NS:.metadata.namespace,NAME:.metadata.name,UID:.metadata.uid,VOLUME:.spec.volumeName,STATUS:.status.phase
```

1. Confirmar UID, fase todavía Released, Retain, servidor y ruta exactos. Correlacionar
   claimRef namespace/name/**UID** con PVCs actuales y eventos/historia Git.
   Un PVC nuevo con el mismo nombre no es el mismo dueño.
2. Identificar autor y finalidad del despliegue/checkpoint; comprobar referencias
   en workloads actuales y otras monturas NFS externas, no solo PVCs del cluster.
3. El operador NAS revisa metadatos de la ruta, montajes, tamaño/fechas y dueño
   con acceso autorizado; no publicar contenido ni asumir que una ruta antigua
   está abandonada. No modificar permisos ni abrir DB en caliente.
4. Verificar copia independiente restaurable y aprobar por escrito retención,
   clasificación de datos y plazo de cuarentena. Si no hay backup o dueño claro,
   dejar el PV/datos intactos y registrar pendiente.
5. Decidir por separado eliminación del **objeto PV** y disposición de los **datos
   NFS**. Retain normalmente conserva los datos al quitar el PV; comportamiento
   de provisioner/finalizers debe confirmarse. Borrar el objeto puede perder
   información necesaria para rebind. No quitar finalizers ni cambiar Retain a
   Delete para forzar limpieza.
6. Tras autorización específica, el operador usa el nombre/UID exacto aprobado;
   este runbook no incluye borrado automático. Conservar metadatos no sensibles
   para recuperación/rebind y validar consumidores después de cada decisión.
   Rebind o restaurar requieren un plan independiente y no son rollback automático.

No eliminar directorios NAS basándose solo en Released, etiquetas, antigüedad,
prefijo `pvc-` o nombres de diagnóstico. Este cambio no autoriza ninguna limpieza.
