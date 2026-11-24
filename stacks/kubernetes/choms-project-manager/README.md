# Operación de CHOMS Project Manager

La aplicación utiliza un Deployment con Flask/Gunicorn y migración inicial,
un StatefulSet PostgreSQL 17 con un PVC RWO de 2 GiB, dos servicios
ClusterIP y políticas de red con denegación por defecto. El rol de la
aplicación es propietario de su base y carece de permisos administrativos del
servidor. Los Pods carecen de token de ServiceAccount. Las sondas separan
proceso y disponibilidad de la base. Para operación diaria, comprobar
rollout, endpoints, uso del PVC y logs con `kubectl -n choms-project-manager`.
Las métricas de infraestructura corresponden al sistema de monitorización
existente. No se incluyen endpoints propios de métricas ni alertas dedicadas.

## Despliegue

1. Construir desde el directorio de la aplicación con `docker build`. Publicar
   su código empaquetado en un registro accesible por K3s y conservar la
   referencia con digest. Los datos iniciales y las credenciales se excluyen
   del build. La referencia publicada para 0.1.0 es
   `ghcr.io/chomsmaster/choms-project-manager@sha256:295e681bf2d0269878e23f94da21cc912bf8e375cf624da57833d4324f859c13`.
   La descarga privada requiere un Secret `kubernetes.io/dockerconfigjson`
   de lectura en el namespace. Usar `PROJECT_IMAGE_PULL_SECRET` para indicar
   su nombre al script. Ejecutar `deploy.sh namespace-plan` y revisar el
   diff antes de `deploy.sh namespace-apply`.
2. Aprovisionar Secrets fuera de Git mediante archivos privados y
   `kubectl create secret generic --from-file`. En `career-db-admin` va
   `password`; en `career-app`, `PGPASSWORD`, `CAREER_ALLOWED_USER`
   y, si se usa MCP, `CAREER_API_TOKEN` de al menos 32 caracteres. El nombre
   de usuario debe coincidir exactamente con la identidad de Authelia.
   En `career-seed` va `seed.json.gz` si hay un primer proyecto que importar.
   Los archivos de valores simples se guardan sin salto de línea final.
3. Revisar `deploy.sh plan IMAGEN@sha256:DIGEST` y ejecutar
   `deploy.sh apply IMAGEN@sha256:DIGEST` con el mismo digest. La migración
   es idempotente. Kubernetes reinicia el contenedor de migración si
   PostgreSQL aún está inicializando.
4. Antes de activar las rutas, verificar que `career.chomsmaster.com` esté
   cubierto por un certificado del listener `websecure`, que Authelia
   autorice al usuario y que Traefik pueda llegar a la aplicación y al
   servicio de identidad. Revisar `deploy.sh edge-plan` y ejecutar
   `deploy.sh edge-apply`. Comprobar redirección a HTTPS, certificado,
   HTTPRoute Accepted/ResolvedRefs, acceso anónimo y con cabecera falsificada
   denegado, acceso autorizado y bloqueo desde un Pod ajeno. Confirmar
   persistencia tras recrear el Pod de aplicación y revisar `kubectl diff`.

Para cerrar el acceso, retirar únicamente las dos HTTPRoutes dedicadas. Para
revertir la aplicación, reaplicar el último digest conocido con el script y
verificar rollout, endpoints y datos. Comprobar antes la compatibilidad con
el esquema aplicado. Conservar el StatefulSet, PVC y Secrets. El
StorageClass local-path puede eliminar el volumen al borrar el PVC.

## Backup y restauración

`backup.sh DIRECTORIO_PRIVADO` realiza un dump lógico de PostgreSQL,
valida que tenga un catálogo restaurable y genera SHA-256. Usar un
destino cifrado con copia fuera del nodo. El dump incluye la configuración
y las planificaciones persistidas. Custodiar credenciales y archivos fuente
privados en su almacén autorizado. El backup manual no configura un horario
ni sustituye la verificación periódica de restauración.

Para restaurar, comprobar `sha256sum -c` y aprovisionar una instancia
PostgreSQL aislada con el rol y una base nueva. Con un cliente de la misma
versión mayor, ejecutar `pg_restore --exit-on-error --single-transaction
--no-owner -d BASE_NUEVA ARCHIVO` autenticado con el rol de la aplicación.
Usar un entorno aislado sin la ruta pública. Comprobar migraciones,
recuentos esperados, visibilidad por proyecto, acceso a tareas y registro
de prueba. Solo tras validar, programar el cambio de conexión y conservar
la base anterior para volver atrás. Nunca restaurar sobre la base activa.

## MCP interno

Ejecutar `kubectl -n choms-project-manager port-forward --address 127.0.0.1
svc/choms-project-manager 18080:8080` con un operador autorizado y pasar el token de
automatización al proceso stdio desde el almacén de secretos. La API verifica el
token. El cliente usa `project_mcp.py` y elige el ámbito mediante
`project_id`. No se publica un endpoint MCP ni se modifica Hermes.
