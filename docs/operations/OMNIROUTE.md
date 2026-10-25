# OmniRoute privado — operación y rollback

Estado 25-10-2026: **ACTIVO; CHECKS RUNTIME NOMBRADOS PASS**.
OmniRoute y Redis están 1/1 Ready en choms-node-02, sin reinicios. Los digests
corresponden a los declarados; PVC Bound y PV Retain con afinidad al mismo nodo.
El certificado está Ready con el SAN nuevo y conserva los SAN anteriores.
Authelia validó la regla exacta con default deny y completó un rollout controlado.
Dashboard/administración devuelven 302 a Authelia; Home/Prometheus conservan ese
contrato y Grafana conserva su autenticación propia con 302 a /login.

Se corrigió exclusivamente el origen CNI de la política del API:
`10.42.0.1/32` → `10.42.0.0/32`. La ruta de node-01 selecciona esta última por
flannel.1. YAML, estructura, selector, TCP/20129, revisión sensible, dry-run y
comparación live verificaron que no cambiase otro campo ni otra política.
Tras aplicar, node-01 → PodIP y node-01 → ClusterIP devolvieron HTTP 401 con
transporte correcto; el túnel desde node-dev-01 también devolvió 401 y se cerró.
No se envió ni leyó ninguna API key; no se leyeron bodies HTTP ni headers sensibles.
El listener 0.0.0.0:20129 está confirmado; /v1 público devuelve 404 y ninguna
regla del hostname con backend selecciona ese path o el puerto API.

La corrección DNS de cert-manager aplicada anteriormente se conserva. Este cierre
no modificó cert-manager, CoreDNS, Traefik, Gateway ni ClusterIssuer. La aserción
anónima del primer intento sigue sin poder identificarse retrospectivamente;
no se reescribe como diagnóstico demostrado. Los fallos posteriores del acceso
desde node-01 se resolvieron con el cambio /32 y su prueba positiva.
No se configuraron proveedores ni se invocaron modelos. La validación local
final se ejecuta una sola vez al cierre y su resultado se entrega en el informe.

## Versión y contrato verificados

Release oficial fijada y verificada para esta preparación: [v3.8.52](https://github.com/diegosouzapw/OmniRoute/releases/tag/v3.8.52).
Docker Hub publica **3.8.52**, sin prefijo v; el tag v3.8.52 devuelve 404.

| Componente | Imagen fijada por digest OCI |
|---|---|
| OmniRoute base | `diegosouzapw/omniroute:3.8.52@sha256:b08a12e876baa8a5ccadd1ebbe346fe7267dba3b1c9f4fd6bb02070fae41ab6c` |
| Redis separado | `redis:8.6.5-alpine@sha256:cd218f4b106a332c5c992e38a9480bfb9d7e9f8f7b0ec9a0023bfa36d9a408f9` |

Fuentes oficiales del tag:
[Docker](https://github.com/diegosouzapw/OmniRoute/blob/v3.8.52/docs/guides/DOCKER_GUIDE.md),
[headless](https://github.com/diegosouzapw/OmniRoute/blob/v3.8.52/docs/guides/HEADLESS.md),
[healthcheck](https://github.com/diegosouzapw/OmniRoute/blob/v3.8.52/scripts/dev/healthcheck.mjs),
[API key de entorno](https://github.com/diegosouzapw/OmniRoute/blob/v3.8.52/src/lib/db/apiKeys.ts).

La imagen plain corresponde al runtime base, usuario node; no incorpora los CLI
ni Chromium de los perfiles cli/web. Se usa base con dashboard y
`OMNIROUTE_HEADLESS=false`: headless estricto responde 404 al dashboard y por eso
no satisface el requisito de administración desde navegador. No se configuran
proveedores OAuth ni sesiones web, ni se montan credenciales de clientes ni se
habilitan servicios embebidos. El bloqueo de background services conserva el
API bridge, la inicialización de seguridad y el proxy; se desactivan syncs
opcionales y el WebSocket de monitorización. No se publica puerto WebSocket.

## Recursos, secretos y acceso

Namespace omniroute, dos Deployments Recreate monorréplica, dos PVC y dos Services
ClusterIP. OmniRoute usa 20128 para dashboard y 20129 para API bridge; Redis solo
6379 interno. Sin NodePort/LoadBalancer nuevos ni hostPath o namespaces host.
No se modifica la release Helm de Traefik ni se reinician bases existentes.

Dashboard activo: **https://omniroute.chomsmaster.com**.

- API `/v1`: únicamente Service ClusterIP:20129 y `REQUIRE_API_KEY=true`; no se
  declara HTTPRoute/Ingress/NodePort/LoadBalancer para el API.
- Dashboard y administración: 20128 mediante rutas explícitas y ForwardAuth;
  regla exacta one_factor y default deny, validada y activa.
- HTTP redirige a HTTPS usando el Gateway compartido. No se cambia Traefik.
- Acceso desde node-dev-01 por túnel SSH de primer plano, enlazado exclusivamente
  a `127.0.0.1`. El helper versionado `scripts/omniroute-tunnel.sh` descubre por
  SSH el ClusterIP actual y valida la dirección antes de abrir el forward.
  No contiene credenciales ni una IP fija del clúster. El destino SSH debe
  proporcionarse explícitamente y su clave de host ya debe ser conocida.
- NetworkPolicy no sustituye la autenticación por clave y no aísla frente a
  administradores o tráfico de nodo que el CNI exima de sus políticas.

Los Secrets runtime se crean únicamente en la API, desde memoria por stdin SSH,
sin valores en argumentos, archivos o salida. El helper rechaza identidades ya
existentes: no regenerar ni sustituirlas tras un fallo. Referencias declarativas
separadas para OmniRoute y Redis; no contiene credenciales de proveedores.
La clave de entorno está soportada realmente por validateApiKey en esta release;
no se confunde con API_KEY_SECRET, que es otro secreto de la aplicación.

## Aislamiento y disponibilidad

Default-deny ingress/egress en el namespace. Traefik solo alcanza 20128; API
20129 permite únicamente las direcciones /32 declaradas del control plane y su
salida Flannel. Se conserva la dirección LAN autorizada. Después,
OmniRoute alcanza su Redis, DNS alcanza CoreDNS y HTTPS saliente se permite a
IPs públicas excluyendo redes privadas/locales. Redis no tiene egress permitido.
La política HTTP monitor admite únicamente el pod existente de Uptime Kuma.
HTTPS por IP pública no es una allowlist de dominios: requeriría otro contrato
CNI/egress. No afirmar restricción FQDN de proveedores con NetworkPolicy estándar.

UID/GID no root, sin elevación, capabilities ALL eliminadas, RuntimeDefault y
sin token automático de ServiceAccount. Requests/límites conservadores; OmniRoute
heap 1 GiB / límite 2 GiB. Startup/readiness/liveness `/healthz` en 20128, el
healthcheck oficial ligero. Grace period 60 segundos supera los 40 oficiales.
Redis usa PING autenticado sin contraseña en argv y AOF persistente.

## Observabilidad y backup

No se declara ServiceMonitor: no hay contrato Prometheus oficial verificado para
esta release. Probes y alertas genéricas de disponibilidad son la base. Definición
del monitor HTTP según el patrón Uptime Kuma existente: URL interna
`http://omniroute.omniroute.svc.cluster.local:20128/healthz`, HTTP 200, intervalo
60 s. Alta en Kuma pendiente si requiere sesión de su administrador; no se leen
sus credenciales ni se modifica su base de datos. La excepción de red está lista.

PVC independientes choms-omniroute-local/Retain: 2 GiB para /app/data (SQLite, configuración,
estado y futuras credenciales cifradas), 1 GiB para /data de Redis (AOF/caché/cuotas).
SQLite usa WAL: se evita NFS según su contrato. La clase nueva reutiliza
rancher.io/local-path con WaitForFirstConsumer y Retain, sin alterar local-path.
No hay hostPath directo en los Pods. El almacenamiento local liga cada volumen
a un nodo y no es HA ni una copia independiente; los tamaños son solicitudes,
no cuotas del filesystem. Recreate impide dos escritores durante actualización. No borrar ni recrear claims durante rollback.

El próximo inventario Kubernetes de backup, cuando se ejecute, incluirá
recursos/claims/rutas del namespace nuevo, sin Secrets; no se ejecutó aquí. Fuente declarativa y metadatos quedan cubiertos
por Git/inventario; **los datos de estos PVC y las claves runtime aún no tienen
copia independiente ni restore acreditado**. Persistencia/AOF o snapshots internos
SQLite no sustituyen backup. No se modifican timers ni se ejecutan backups/Restic.
Antes de cargar proveedores: autorizar copia consistente de SQLite y sus claves
de cifrado/bootstrap por canales privados; revisar Redis y demostrar restore.

## Añadir proveedores posteriormente

1. Acceder al dashboard por HTTPS y completar Authelia; recuperar la contraseña
   inicial de OmniRoute solo por un canal privado autorizado, sin terminal/logs.
2. En Providers, añadir exclusivamente un proveedor API-key y su clave mediante
   el formulario protegido. No usar OAuth, importaciones de CLI, cookies/web o
   credenciales locales de agentes. No se configuran durante este bloque.
3. No activar pruebas de generación, playground ni tests de modelos sin una nueva
   autorización de gasto. Descubrimiento/health no equivale a inferencia.
4. Revisar copia consistente y custodia de claves antes de almacenar credenciales.
   Para clientes usar una clave propia de OmniRoute, nunca la clave del proveedor.

## Aplicación, comprobaciones y rollback

Solo desde el checkout público verificado main/limpio/sin divergencia. Preflight
acotado de namespace, hostname, Gateway/TLS, storage y autenticación. Dry-run
servidor y diff antes de aplicar los nuevos recursos. Namespace primero; helper
runtime solo con autorización explícita y sin Secret previo. Después recursos
nuevos, regla validada de Authelia, único rollout Authelia y ampliación TLS mínima.

El certificado y CM live contienen extensiones ajenas al alcance público. Para
no retirarlas, no reaplicar su manifiesto completo: añadir únicamente SAN/regla
con patch y comprobación de concurrencia, preservando el resto. El JSON patch
TLS se aplica solo si falta el SAN; no repetir add a ciegas. Guardar configuración
anterior de ambos y anotación de rollout fuera de Git, sin Secret values.

Authelia 4.39.20 expone `config validate`, sin comando de recarga segura de ACL.
Validar YAML y `authelia config validate` en el workload con su configuración de
ejecución antes del rollout. Comprobar Ready y redirecciones de rutas protegidas
existentes; ante fallo restaurar inmediatamente solo la regla y su rollout.
No tocar Redis compartido, bases ni otros workloads.

Comprobar ambos Pods Ready, PVC Bound, EndpointSlices Ready, TLS válido, challenge
Authelia en dashboard y rechazo /v1 anónimo. Se ha demostrado HTTP 401 sin
clave por PodIP, ClusterIP y túnel; no se realizó descubrimiento autenticado.
Probar denegación efectiva desde un pod temporal sin permisos hacia app/Redis,
DNS/Redis/HTTPS autorizados y egress privado denegado desde OmniRoute; estas pruebas
negativas completas siguen pendientes; las pruebas positivas del API y túnel
sí se acreditaron en este cierre. El pod de
prueba no monta Secret ni PVC y se elimina al terminar.

Rollback del servicio: retirar únicamente sus HTTPRoutes/Middleware, escalar a
cero sus dos Deployments y preservar namespace, PVC y Secrets. Revertir solo el
SAN nuevo y la regla nueva con pruebas de concurrencia, restaurar la anotación
previa de Authelia y esperar Ready. Nunca delete namespace, PVC, Secret ni datos.
No usar apply recursivo de stacks/ ni rollback global de Helm. Ante un fallo,
detenerse sin commit/push y conservar evidencia sanitizada para revisión.

## Evidencia y siguiente límite

YAML, Helm template v1.21.1, comparación exacta de 51 objetos release/hooks,
rollback renderizado retirando solo el argumento, flujo filtrado con fixtures,
Bash/ShellCheck y revisión local acotada comprobados. No se reejecuta el flujo
global de releases ni se cambia ClusterIssuer, Gateway, provider o puertos.

El cierre acredita los checks runtime nombrados: certificado, SAN nuevo y
anteriores, Authelia y rutas existentes, Pods Ready/nodo/reinicios/digests,
PVC/PV, Accepted/ResolvedRefs, redirección del dashboard, /v1 no publicado,
ClusterIP:20129, rechazo sin clave, Services internos y endpoints Ready.
El ClusterIP se descubre en cada ejecución; cliente local:
`http://127.0.0.1:20129/v1`, solo mientras el operador mantenga el helper abierto.
Redis no tiene exposición externa. No hay aceptación de restore ni pruebas de
inferencia.

### Uso del túnel

```bash
./scripts/omniroute-tunnel.sh operador@control-plane.example
# Alternativa: export OMNIROUTE_SSH_TARGET=operador@control-plane.example
# ./scripts/omniroute-tunnel.sh
# Puerto local alternativo: ./scripts/omniroute-tunnel.sh operador@control-plane.example 20130
```

El destino debe permitir `kubectl get service` sin sudo. No se copian kubeconfigs
ni se incluyen API keys o contraseñas. El puerto local predeterminado es 20129
(también configurable con `OMNIROUTE_LOCAL_PORT`); el destino API siempre es
20129. SSH usa BatchMode, StrictHostKeyChecking y ExitOnForwardFailure, y queda
en primer plano. **Cerrar con Ctrl+C** termina el proceso SSH y el túnel.
El helper admite ClusterIP IPv4 unicast; falla de forma cerrada ante respuestas
vacías, direcciones inválidas o una instalación exclusivamente IPv6.

Una consulta sin clave que devuelve **401 o 403** demuestra que ese endpoint
requiere autenticación; no demuestra acceso autorizado ni funcionalidad de un
proveedor. Las pruebas PodIP, ClusterIP y túnel realizadas devolvieron 401 sin
leer cuerpos ni claves. La revisión del helper versionado usa pruebas sintéticas
sin abrir conexiones SSH; no se repite el túnel live durante el cierre en Git.

El bootstrap runtime sigue limitado a la instalación inicial: exige un destino
explícito en `OMNIROUTE_SSH_TARGET`, rechaza Secrets existentes y no debe
ejecutarse para reanudar el servicio. No contiene una dirección SSH fija.

Rollback de la corrección DNS: retirar exclusivamente el argumento agregado en
`stacks/kubernetes/cert-manager/values.yaml`, renderizar con el mismo chart y
exigir que solo cambien los args del controller; usar el flujo versionado
`plan cert-manager` / `apply cert-manager`. No modificar CoreDNS ni otros valores.
Backup independiente de PVC y claves runtime, restore controlado y monitor Kuma
siguen pendientes. La persistencia local y AOF no sustituyen un backup.
