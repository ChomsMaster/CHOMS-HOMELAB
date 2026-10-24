# NetworkPolicies: propuesta y adopción por namespace

Preparación local del 23-10-2026; **no desplegada**. Fuente de estado real:
inventario facilitado por el propietario, 18 namespaces y ninguna NetworkPolicy.
Hay 13 carpetas; se excluyen default, kube-system, kube-public y kube-node-lease.
No es una certificación de conectividad: faltan labels y targetPorts renderizados
de Helm, endpoints de API y comportamiento CNI/SNAT observados.

## Contrato de tráfico

Cada carpeta incluye deny ingress/egress, DNS exclusivamente hacia CoreDNS
(`k8s-app=kube-dns`, TCP/UDP 53) y excepciones explícitas. Los pares entre
namespaces tienen permiso de salida e ingreso en ambos extremos. Los permisos
de Prometheus usan `app.kubernetes.io/name=prometheus`, no todo monitoring.
Solo se abren puertos de métricas identificados; apps sin endpoint conocido no
reciben un permiso ficticio. Añadir un ServiceMonitor exige revisar ambos lados.

| Flujo | Destino efectivo del Pod | Evidencia / límite |
|---|---|---|
| Traefik → home, Nextcloud, Filebrowser | TCP 80 | Manifiestos existentes |
| Traefik → controller / Portainer / Kuma | 8000 / 9000 / 3001 TCP | targetPort resuelto, no port 80 del Service |
| Traefik → Authelia | TCP 9091 | ForwardAuth y Service |
| Traefik → Colegio / Scrutiny | TCP 8080 | Services y containerPorts |
| Traefik → Jellyfin | 8096 TCP | Manifiestos existentes |
| Traefik → Grafana / Prometheus | 3000 / 9090 TCP | Supuesto del chart, confirmar render |
| Internet → Traefik | 8000 / 8443 TCP | Values: Service publica 80/443 |
| Traefik → solver ACME | TCP 8089 | Label/puerto habitual de cert-manager; confirmar |
| apps → databases | 3306, 5432, 6379 TCP | Permiso inicial por namespace; reducir por consumidor confirmado |
| Colegio → sus dos MariaDB | TCP 3306 | Incluye CronJob sin labels en su template |
| Authelia → Redis | TCP 6379 | Manifiestos |
| Alloy/canary/gateway/Loki internos | 80, 8080, 3100, 9095, 9096, 7946 TCP; 7946 UDP | Límite al namespace logging; 8080 supuesto targetPort gateway |
| Grafana → Loki / Prometheus | 80/8080/3100 y 9090 TCP | Queries/datasource |
| Prometheus → métricas | 9402, 12345, 3100, 3500, 4040, 7472, 8080, 8081, 9090, 9093, 9100, 10250 según namespace | Puertos chart a confirmar; 8080 se comparte con APIs, no es control HTTP de ruta |
| Prometheus → NAS/nodos/CoreDNS | 9100, 7472, 10250, 4194, 10255; CoreDNS 9153 TCP | Inventario y values de NAS; revisar necesidad de puertos legacy |
| API server → webhooks | cert-manager/operador 10250; MetalLB 9443 TCP | Targets de charts por confirmar; fuente nodos y kube-system |
| Controladores → API Kubernetes | 10.43.0.1:443 / 192.168.1.138:6443 | Service observado/control-plane; DNAT/CNI no verificado |
| Provisioner → NAS | 192.168.1.167:2049 TCP | NFSv4 supuesto; RPC/mountd de NFSv3 no permitido |
| Scrutiny → InfluxDB / collectors → Scrutiny | 8086 / 8080 TCP | Backend dividido y backup lógico |
| Prometheus → Alertmanager; gossip | 9093; 9094 TCP/UDP | Labels chart por confirmar |

Alertmanager tiene HTTPS público para Telegram y cert-manager para ACME.
Nextcloud (marketplace/actualizaciones) y Kuma (sondas HTTPS) tienen excepciones
separadas por app. Se excluyen redes RFC1918 y link-local de esas excepciones.
NetworkPolicy estándar no permite limitar por FQDN: HTTPS significa cualquier IP
pública en 443, no solo el dominio de Telegram/ACME. Evaluar proxy de salida/CNI
con FQDN antes de endurecer. No se permite HTTP público general ni IPv6.

**Las imágenes las descarga kubelet/containerd desde el host**, no los Pods:
no se abre internet en cada namespace para image pulls. Políticas de host y
acceso a registries son un control distinto. El montaje NFS de PVC lo efectúa
normalmente kubelet; la regla del provisioner no demuestra protección de esos
montajes. hostNetwork (speaker/node-exporter) y tráfico originado por nodos
pueden quedar fuera de NetworkPolicy según CNI. No afirmar aislamiento del host.

## Supuestos y puertas de entrada

Antes de ejecutar, confirmar con autorización independiente: CNI que haga cumplir
NetworkPolicy, namespace labels estándar, labels reales de charts, targetPorts,
API endpoints tras DNAT, DNS tras DNAT y admission webhooks. Un manifiesto válido
por schema no demuestra que la política funcione. El inventario no contiene
estos detalles; por ello la propuesta **no está lista para aplicar a ciegas**.

Kuma puede requerir sondas LAN/HTTP o protocolos adicionales; no se han inventado
sus destinos. La aplicación controller puede tener dependencias adicionales.
defecto; documentar destinos y decisión del propietario antes de esos namespaces.
Apps tienen acceso a las tres DB como transición explícita, pendiente reducir.
El colector NAS consume la ruta HTTPS existente de Scrutiny; la excepción LAN
directa 8080 es opcional y debe retirarse si no hay consumidor directo aprobado.
Metallb memberlist 7946 no se considera corregido por estas políticas: el roadmap
registra un rollback y diagnóstico previo bloqueado; no mezclar reconciliaciones.

## Orden y comprobaciones del operador (no ejecutadas aquí)

1. Revisar supuestos, labels/targets y matriz por consumidor. Guardar fuera de Git
   evidencia no sensible de DNS, login, rutas, métricas y Jobs antes de cambiar.
   Mantener una sesión alternativa con permisos para revertir NetworkPolicies.
2. Empezar por `colegio-maria-rosario-staging`: es un único namespace aislado de
   datos de producción. Verificar web/Moodle/Gibbon, conexión DB y cron exitoso.
3. Continuar de uno en uno: diagnostics, filebrowser, apps, security, databases,
   media, logging, monitoring, nfs-provisioner, cert-manager,
   metallb-system y traefik al final. Detenerse donde falte un consumidor conocido.
4. Cada paso: `./scripts/netpol-rollout.sh --execute CONTEXTO NAMESPACE`.
   El script rechaza políticas preexistentes, hace server dry-run, instala
   excepciones antes del deny y muestra el rollback exacto. No lo ejecuta CI.
5. Después de cada paso: comprobar DNS desde consumidores, HTTPS y ForwardAuth,
   lecturas/escrituras sintéticas autorizadas de DB, nuevo Job cron, targets
   Prometheus UP, queries de Grafana/Loki, logs de Alloy y backup lógico.
   Para infraestructura: webhook admission, solver/renovación controlada, nuevo
   PVC de prueba independiente y memberlist/estado L2. Esas pruebas requieren
   autorización operacional; no se realizaron durante la preparación de código.
6. Comprobar ambos extremos cuando el destino todavía no tenga deny. Las
   políticas son aditivas: una regla más amplia puede anular el efecto deseado.
   Repetir checks de consumidores ya migrados antes del siguiente namespace.

## Rollback

El script está limitado a primera instalación y exige cero políticas previas.
Si falla apply o una comprobación, no avanzar. Usar el comando exacto impreso:

```bash
kubectl --context CONTEXTO -n NAMESPACE delete -f stacks/kubernetes/networkpolicies/NAMESPACE/policies.yaml
```

Esto elimina solo los nombres introducidos, restableciendo el estado sin
políticas del inventario; no borra Pods, PVCs, PVs ni otras configuraciones.
Conservar el mismo commit/archivo durante aplicación y rollback. Si ya había
políticas o cambió su ownership, no usar este procedimiento: preparar migración
y copia de las políticas originales, sin exportar Secrets.
