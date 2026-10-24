# Reconstrucción de CHOMS Platforms

Procedimiento para una **tarea de recuperación autorizada**, no ejecutado aquí.
No reemplaza una prueba de restauración. Fuente de topología: baseline del
23-10-2026. Kit privado descrito en [RECOVERY_KIT.md](RECOVERY_KIT.md).

## Condiciones antes de empezar

Elegir commit público y kit del mismo checkpoint; disponer de la clave age por
custodia independiente, token original K3s, versión y tipo de datastore reales,
variables Ansible, configuración de red y acceso físico/administrativo seguro.
Abrir tmpfs privado 0700 para descifrado; archivos 0600, sin shell tracing,
transcripciones, CI ni volcados en terminal. Nunca descifrar dentro de Git.
Verificar fuentes de datos/NFS y backups de aplicaciones por separado: **el kit
no contiene sus datos**. No arrancar DBs sobre directorios nuevos/vacíos pensando
que recuperar objetos Kubernetes equivale a recuperar datos.

Secuencia primaria: recuperar el datastore original consistente del servidor
SQLite, conservando token e identidad. Si la metadata indica etcd, detenerse y
usar la restauración soportada para esa versión; no copiar un snapshot etcd como
state.db. External datastore no está cubierto por este kit.

## 1. Ansible: sistema y dependencias

1. Recuperar hardware/VMs, instalar Debian 13 y restaurar red/DNS/NTP según notas
   privadas; mantener endpoints públicos cerrados mientras se reconstruye.
2. Recuperar del artefacto age opaco correspondiente las variables de Ansible
   hacia fichero 0600 en tmpfs, según el mapa custodiado por el operador. Revisar
   inventario no sensible y confirmar destinos antes de usarlo.
3. Desde `ansible/`, ejecutar con el archivo privado externo:

```bash
ansible-playbook -i inventories/homelab/hosts.yml playbooks/bootstrap-node.yml --extra-vars @/RUTA_TMPFS/ansible-vars.yml
```

El rol actual solo cubre paquetes, timezone y timesyncd: **no** instala K3s,
no reconstruye NAS/RAID ni restaura datos. Preparar NAS/NFS y sus exportaciones
mediante su procedimiento independiente. Verificar UID/GID, permisos, rutas y
contenido antes de habilitar mounts de producción. No formatear discos existentes.

## 2. K3s: recuperar datastore y bootstrap

1. Instalar exactamente la versión guardada en metadata con su procedimiento
   soportado y artefactos verificados. El baseline histórico es v1.36.2+k3s1;
   no usarlo si el snapshot proviene de otra versión. No instalar latest.
2. Con servidor detenido y sin agentes reconectando, descifrar token y datastore
   a tmpfs y restaurar el token original en su ruta protegida. Comprobar si se
   requiere encryption-config original; si falta y la metadata lo exige, abortar.
3. Para el servidor SQLite, restaurar la copia consistente al data-dir real
   (`server/db/state.db` bajo el data-dir estándar), con propietario/modos del
   servicio. Preservar estado anterior fuera de esa ruta para rollback; no mezclar
   archivos WAL/SHM de una instalación anterior con la copia consistente.
   Confirmar flags, rutas y compatibilidad con la versión instalada antes de copiar.
4. Arrancar el único servidor, comprobar API, controladores base, CoreDNS y
   local-path. Recuperar agentes con token y endpoint del servidor por un canal
   privado; nunca poner tokens en argumentos publicados, Git o logs. Confirmar
   tres nodos Ready e identidades esperadas. No crear un segundo control-plane
   fingiendo que convierte esta topología SQLite en HA.
5. La recuperación del datastore **ya trae namespaces, CRDs, objetos y Secrets**.
   Mantener workloads con datos no recuperados detenidos durante la recuperación
   mediante un plan operacional registrado. No borrar recursos en masa.

Un snapshot no demostrado consistente, credenciales bootstrap perdidas o NFS sin
datos restaurados son bloqueos reales. Este runbook no los resuelve por inferencia.

## 3. Terraform / Helm: restablecer ownership antes de cambiar

1. Inspeccionar lo que volvió del datastore y confirmar que existen las CRDs
   Gateway API y demás prerequisitos antes de reconciliar Helm. Si faltan,
   recuperarlas desde la fuente aprobada antes de continuar (véase paso 4).
   Las seis releases pueden existir
   ya; **no instalar duplicados** ni aplicar Terraform sobre estado vacío.
2. Elegir un único escritor. Para Terraform, configurar autenticación externa y
   endpoint real, inicializar backend según política del propietario y ejecutar
   los 20 imports de [IMPORT.md](../../terraform/environments/homelab/IMPORT.md).
   El kit no incluye tfstate: reconstruir ownership mediante imports si se perdió.
3. Revisar plan privado. Abortarlo si intenta recrear namespaces, cambiar PVCs,
   destruir releases o introducir upgrades. No apply automático por haber pasado
   terraform validate. Charts/versions y orden de values: releases.json.
4. Si se elige Helm directo, no usar Terraform para escribir esos mismos releases.
   Reconciliar por dependencia: NFS → cert-manager → Traefik → monitoring → Loki
   → Alloy, tras comprobar Secrets/referencias requeridos y CRDs. El instalador
   histórico procesa esos componentes, pero no sustituye revisión por release.

**Alternativa sin recuperar datastore:** crear primero namespaces y Secrets de
bootstrap revisados del paso 5, además de los CRDs necesarios. Solo después
instalar releases que los consumen. Monitoring/Grafana y sus values requieren
Secrets externos; el wait/atomic de Helm fallará si se pospone ese bootstrap.
No existe una secuencia correcta que espere al final para crear esas credenciales.

## 4. Manifiestos: infraestructura antes que consumidores

1. Confirmar Gateway API CRDs compatibles y ownership antes de Traefik. Si se
   reconstruye desde cero, instalar CRDs aprobadas desde su fuente bloqueada;
   el repo no demuestra por sí solo el bootstrap completo de Gateway API.
2. Revisar MetalLB nativo/versionado, después address-pool. El speaker conserva
   diagnóstico bloqueado: no forzar su rollout para resolver una referencia tag.
3. Reconciliar split DNS, issuer y Certificate después de Gateway/CRDs. Mantener
   control de exposición mientras DNS público y certificados no estén verificados.
4. Reconciliar namespaces y configuración de seguridad/Authelia; después DBs,
   aplicaciones y observabilidad directa. Revisar cada archivo con validación
   local y diff autorizado antes de apply. No usar `apply -R stacks/kubernetes`:
   mezcla values, plantillas de políticas propuestas y recursos de ownership distinto.
5. PVCs/PVs: comparar claimRef UID, export/ruta y datos reales antes de cualquier
   cambio. Los PVs Released/Retain no se reciclan ni se borran automáticamente.
6. HTTPRoutes/ForwardAuth y certificados antes de abrir router/NAT. Mantener
   NetworkPolicies propuestas sin aplicar hasta comprobar CNI/labels/puertos y
   ejecutar su rollout independiente por namespace. No mezclarlo con recuperación.

## 5. Secrets y configuración: reconciliar, no reinyectar ciegamente

Este paso es la revisión final de credenciales que ya pudo requerirse en los
pasos 2–3. Si un Secret faltaba para bootstrap, debe haberse recuperado antes
de arrancar su consumidor. Descifrar únicamente entradas seleccionadas a tmpfs
o pipes, nunca al terminal ni al repositorio.

1. Del listado cifrado escoger namespace/nombre/tipo vigentes; quitar en memoria
   UID/resourceVersion/managedFields/status y metadata de otro clúster. Comprobar
   coherencia con nombres de referencia en los values/manifiestos.
2. No reaplicar todo el export como un bloque. Reconciliar Secrets de aplicación
   por grupo y propietario. No reintroducir Helm history Secrets sobre una nueva
   release, tokens de ServiceAccount antiguos, contraseñas de nodo de otra
   identidad, ni certificados de webhook cuya CA ya se regeneró. Cert-manager y
   operadores deben reconciliar sus objetos según su lifecycle.
3. Reponer configuración y, si procede, identidades de Authelia mediante su
   contrato ConfigMap/Secret; preservar claves de sesión/cifrado si hay estado
   dependiente. Validar configuración sin imprimirla antes de reiniciar consumidores.
4. Instalar contraseña Restic desde el kit en custodia local protegida, restaurar
   configuración de acceso al repositorio existente y verificar que se accede al
   repositorio correcto. **No hacer restic init sobre un repositorio ya existente.**
5. Reponer notas operacionales privadas y variables Ansible; guardar solo evidencia
   agregada de recuperación en Git. La custodia de la clave age sigue externa.

## 6. Verificación, aceptación y rollback

1. Nodos Ready; DNS interno/externo, reloj, API, storage y rutas consistentes.
2. PVCs Bound y **datos recuperados**; DBs con probes e integridad, lecturas y
   escrituras sintéticas aprobadas. Restaurar datos por runbooks independientes
   cuando no se conserve el NAS/disco original; kit por sí solo no basta.
3. Seis releases con charts previstos; deployments/sts/ds listos; CronJobs con
   ejecuciones nuevas exitosas. Los nueve Pods Error antiguos no son éxito nuevo.
4. Gateway Accepted/Programmed; HTTPRoutes ResolvedRefs; TLS/renovación; login
   Authelia y denegación/redirección anónima donde corresponda.
5. Targets Prometheus UP, queries Grafana/Loki, Alloy publicando y notificación
   crítica/resuelta controlada sin mostrar credenciales. Backup nuevo y prueba
   aislada de restauración; no confundir ejecución exitosa con RPO de datos útiles.
6. Medir RPO/RTO, registrar versión/commit/checkpoint y resultado sin datos.
   Solo entonces abrir exposición pública y aceptar la reconstrucción.

Si una fase falla, no avanzar. Preservar datastore/discos anteriores, rollback
por release/archivo y evidencia mínima; no sobrescribir backups ni borrar PVs.
Limpiar tmpfs al terminar según política del operador. Prueba integral pendiente:
este documento es un procedimiento preparado, no prueba de reconstrucción realizada.
