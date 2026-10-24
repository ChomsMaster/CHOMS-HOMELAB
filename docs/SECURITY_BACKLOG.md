# Backlog de seguridad

Trivy es **informativo**, no bloquea validate.sh ni CI por hallazgos o por su
indisponibilidad. Los demás validadores conservan su semántica de fallo. No se
ocultan reglas ni se modifican manifiestos para satisfacer el scanner.

Referencia pública tras la separación: **56 hallazgos: 1 CRITICAL aceptado y 55 HIGH**.
Se trasladaron cinco hallazgos junto con sus extensiones; no son vulnerabilidades
corregidas ni un cambio en producción. Un hallazgo de scanner requiere análisis,
no es prueba automática de explotación.

## Tipos, ordenados por prioridad

| Tipo / regla | Severidad | Recuento | Acción pendiente |
|---|---|---:|---|
| Gestión de webhookconfigurations (RBAC MetalLB) (KSV-0114) | CRITICAL | 1 | Riesgo aceptado; revisar al actualizar MetalLB |
| Acceso a red del host (KSV-0009) | HIGH | 1 | Revisión por recurso e imagen, sin rollout automático |
| Filesystem raíz escribible (KSV-0014) | HIGH | 20 | Revisión por recurso e imagen, sin rollout automático |
| Contenedores privilegiados (KSV-0017) | HIGH | 2 | Revisión por recurso e imagen, sin rollout automático |
| Contexto de seguridad por defecto (KSV-0118) | HIGH | 30 | Revisión por recurso e imagen, sin rollout automático |
| Capability NET_RAW (KSV-0119) | HIGH | 1 | Revisión por recurso e imagen, sin rollout automático |
| Volúmenes del host no permitidos por la regla (KSV-0121) | HIGH | 1 | Revisión por recurso e imagen, sin rollout automático |

## CRITICAL primero: RBAC de MetalLB

KSV-0114: **riesgo aceptado**, no vulnerabilidad corregida. El controlador
necesita gestionar la `ValidatingWebhookConfiguration`; este permiso procede del
manifiesto oficial actualmente adoptado. Retirarlo sin pruebas rompería la
reconciliación. Se conserva el finding CRITICAL y el manifiesto sin cambios.
Responsable de la aceptación: propietario de plataforma, por instrucción de este
encargo. **Revisar nuevamente al actualizar MetalLB**, comprobando permisos y
reconciliación en un entorno de prueba.

## HIGH: plan por tipo

1. Contextos de seguridad (30): comprobar herencia del Pod y entrypoint real,
   UID/GID, capabilities y volúmenes antes de cambiar controles por contenedor.
2. Filesystem raíz (20): identificar rutas escribibles, tmp/config/cache y
   permisos de PVC; no imponer readOnlyRootFilesystem a DBs sin pruebas aisladas.
3. Privilegios (2): Jellyfin y colectores Scrutiny; diseñar acceso por dispositivo
   soportado. El roadmap registra limitaciones de cgroups/device mapping.
4. Red del host (1): distinguir L2/monitorización de exposición de
   aplicaciones; verificar necesidad y frontera efectiva del CNI.
5. NET_RAW (1): validar dependencia L2 y reducir solo con evidencia funcional.
6. Volúmenes de host (1): limitar mounts/derechos sin romper lectura de dispositivos.

Cada cambio futuro requiere propietario, pruebas de imagen/consumidores/storage,
rollback y aceptación operacional. El modo informativo es una política de CI,
no una aceptación de riesgo ni una afirmación de que la plataforma esté endurecida.

## Recursos afectados (sin contenido ni valores)

| Archivo | Línea del informe base | Regla | Severidad |
|---|---:|---|---|
| `stacks/kubernetes/metallb/metallb-native-v0.15.2.yaml` | 1612 | KSV-0114 | CRITICAL |
| `stacks/kubernetes/metallb/metallb-native-v0.15.2.yaml` | 1879 | KSV-0009 | HIGH |
| `stacks/kubernetes/apps/nextcloud.yaml` | 57 | KSV-0014 | HIGH |
| `stacks/kubernetes/apps/nextcloud.yaml` | 129 | KSV-0014 | HIGH |
| `stacks/kubernetes/apps/portainer.yaml` | 203 | KSV-0014 | HIGH |
| `stacks/kubernetes/apps/uptime-kuma.yaml` | 55 | KSV-0014 | HIGH |
| `stacks/kubernetes/authelia/authelia.yaml` | 70 | KSV-0014 | HIGH |
| `stacks/kubernetes/colegio-staging/gibbon.yaml` | 40 | KSV-0014 | HIGH |
| `stacks/kubernetes/colegio-staging/gibbon.yaml` | 139 | KSV-0014 | HIGH |
| `stacks/kubernetes/colegio-staging/gibbon.yaml` | 155 | KSV-0014 | HIGH |
| `stacks/kubernetes/colegio-staging/moodle.yaml` | 46 | KSV-0014 | HIGH |
| `stacks/kubernetes/colegio-staging/moodle.yaml` | 96 | KSV-0014 | HIGH |
| `stacks/kubernetes/colegio-staging/moodle.yaml` | 106 | KSV-0014 | HIGH |
| `stacks/kubernetes/databases/mariadb.yaml` | 54 | KSV-0014 | HIGH |
| `stacks/kubernetes/databases/postgres.yaml` | 59 | KSV-0014 | HIGH |
| `stacks/kubernetes/databases/redis.yaml` | 54 | KSV-0014 | HIGH |
| `stacks/kubernetes/filebrowser/filebrowser.yaml` | 39 | KSV-0014 | HIGH |
| `stacks/kubernetes/home/home.yaml` | 157 | KSV-0014 | HIGH |
| `stacks/kubernetes/jellyfin/jellyfin.yaml` | 44 | KSV-0014 | HIGH |
| `stacks/kubernetes/scrutiny/collectors.yaml` | 23 | KSV-0014 | HIGH |
| `stacks/kubernetes/scrutiny/server.yaml` | 31 | KSV-0014 | HIGH |
| `stacks/kubernetes/scrutiny/server.yaml` | 63 | KSV-0014 | HIGH |
| `stacks/kubernetes/jellyfin/jellyfin.yaml` | 44 | KSV-0017 | HIGH |
| `stacks/kubernetes/scrutiny/collectors.yaml` | 23 | KSV-0017 | HIGH |
| `stacks/kubernetes/apps/choms-controller.yaml` | 24 | KSV-0118 | HIGH |
| `stacks/kubernetes/apps/nextcloud.yaml` | 55 | KSV-0118 | HIGH |
| `stacks/kubernetes/apps/nextcloud.yaml` | 57 | KSV-0118 | HIGH |
| `stacks/kubernetes/apps/nextcloud.yaml` | 129 | KSV-0118 | HIGH |
| `stacks/kubernetes/apps/portainer.yaml` | 201 | KSV-0118 | HIGH |
| `stacks/kubernetes/apps/portainer.yaml` | 203 | KSV-0118 | HIGH |
| `stacks/kubernetes/apps/uptime-kuma.yaml` | 53 | KSV-0118 | HIGH |
| `stacks/kubernetes/apps/uptime-kuma.yaml` | 55 | KSV-0118 | HIGH |
| `stacks/kubernetes/authelia/authelia.yaml` | 68 | KSV-0118 | HIGH |
| `stacks/kubernetes/authelia/authelia.yaml` | 70 | KSV-0118 | HIGH |
| `stacks/kubernetes/colegio-staging/gibbon.yaml` | 37 | KSV-0118 | HIGH |
| `stacks/kubernetes/colegio-staging/gibbon.yaml` | 40 | KSV-0118 | HIGH |
| `stacks/kubernetes/colegio-staging/gibbon.yaml` | 136 | KSV-0118 | HIGH |
| `stacks/kubernetes/colegio-staging/moodle.yaml` | 43 | KSV-0118 | HIGH |
| `stacks/kubernetes/colegio-staging/moodle.yaml` | 46 | KSV-0118 | HIGH |
| `stacks/kubernetes/colegio-staging/moodle.yaml` | 92 | KSV-0118 | HIGH |
| `stacks/kubernetes/colegio-staging/moodle.yaml` | 189 | KSV-0118 | HIGH |
| `stacks/kubernetes/colegio-staging/moodle.yaml` | 250 | KSV-0118 | HIGH |
| `stacks/kubernetes/databases/mariadb.yaml` | 52 | KSV-0118 | HIGH |
| `stacks/kubernetes/databases/mariadb.yaml` | 54 | KSV-0118 | HIGH |
| `stacks/kubernetes/databases/postgres.yaml` | 59 | KSV-0118 | HIGH |
| `stacks/kubernetes/databases/redis.yaml` | 52 | KSV-0118 | HIGH |
| `stacks/kubernetes/databases/redis.yaml` | 54 | KSV-0118 | HIGH |
| `stacks/kubernetes/filebrowser/filebrowser.yaml` | 39 | KSV-0118 | HIGH |
| `stacks/kubernetes/home/home.yaml` | 146 | KSV-0118 | HIGH |
| `stacks/kubernetes/home/home.yaml` | 157 | KSV-0118 | HIGH |
| `stacks/kubernetes/metallb/metallb-native-v0.15.2.yaml` | 1892 | KSV-0118 | HIGH |
| `stacks/kubernetes/scrutiny/collectors.yaml` | 14 | KSV-0118 | HIGH |
| `stacks/kubernetes/scrutiny/server.yaml` | 25 | KSV-0118 | HIGH |
| `stacks/kubernetes/scrutiny/server.yaml` | 57 | KSV-0118 | HIGH |
| `stacks/kubernetes/metallb/metallb-native-v0.15.2.yaml` | 1870 | KSV-0119 | HIGH |
| `stacks/kubernetes/scrutiny/collectors.yaml` | 6 | KSV-0121 | HIGH |
