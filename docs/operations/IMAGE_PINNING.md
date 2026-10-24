# Inmutabilidad de imágenes: estado y pendientes

Fuente: inventario de producción del 23-10-2026, sin consulta nueva de registry
ni clúster. No se inventan digests ni versiones semánticas a partir de un hash.

- MetalLB speaker: Git ya declara
  `quay.io/metallb/speaker@sha256:260c9406f957c0830d4e6cd2e9ac8c05e51ac959dd2462c4c2269ac43076665a`.
  El inventario observa `v0.15.2` en producción y no comprueba su imageID.
  Se mantiene el digest de Git; correspondencia tag/manifest list/plataforma
  **pendiente de verificación**. El roadmap registra rollback por memberlist y
  L2Status; no hacer apply ni reemplazar tags como solución a ese incidente.
- Authelia sigue en `4.39.20`: obtener de forma autorizada el imageID efectivo,
  comprobar procedencia/multiarquitectura y fijarlo sin actualizar versión.
- Charts: cert-manager, Traefik, Prometheus/operator/Alertmanager/Grafana,
  kube-state-metrics, node-exporter, Loki/canary/sidecars, Alloy y provisioner NFS
  usan tags en varios contenedores. Revisar un release cada vez, incluidos init
  containers. Los charts están bloqueados pero eso no hace inmutables sus tags.
- Workloads de K3s (CoreDNS/local-path/metrics-server): tratar por lifecycle K3s,
  no parchear controladores generados.
- Portainer/Kuma: mismo digest con y sin prefijo docker.io. No es evidencia de
  imágenes distintas; normalización declarativa puede causar rollout.

La tarea futura debe registrar imagen declarada, imageID, arquitectura, digest
de índice frente a digest de manifiesto y firma/procedencia cuando exista.
Validar rutas, storage, consumidores y rollback después de un cambio autorizado.
Este documento no afirma que los digests existentes estén verificados por registry.
