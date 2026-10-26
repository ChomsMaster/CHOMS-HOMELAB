---
name: choms-kubernetes-patterns
description: "Review or author declarative Kubernetes workload, storage, probe, RBAC and network policy changes within the authorized CHOMS scope."
license: MIT
metadata:
  upstream: affaan-m/ECC
  upstream-tag: v2.2.3
  upstream-commit: c05b2d6614f62f6db0047669aa4eefb223d478f9
  upstream-skill: kubernetes-patterns
  adaptation: CHOMS isolated review candidate
---

# Patrones Kubernetes CHOMS
Inspecciona únicamente los manifiestos y patrones relevantes. Verifica selectors, Service/targetPort,
probes oficiales, grace period, recursos, ServiceAccount y automount, securityContext y permisos mínimos.
Para persistencia revisa StorageClass, reclaimPolicy, afinidad y estrategia de actualización compatible
con el volumen: no trasladar ciegamente replicas 2+, HPA o RollingUpdate a RWO monorréplica.
Prefiere ClusterIP para servicios internos y rutas autorizadas existentes. Revisa default-deny,
DNS y flujos mínimos, sin inventar necesidad de exposición o rangos amplios.
Verifica versiones y digests reales; semver no demuestra inmutabilidad. Mantén Secrets runtime fuera
 de Git; no crear --from-literal con valores visibles ni copiar payloads de ejemplos ECC.
La skill prepara o revisa código; kubectl apply/exec/scale/rollback y lecturas live requieren alcance
operativo explícito. Ningún acceso live ocurre por la mera activación. Preserva datos y documenta rollback.

## Límites del perfil CHOMS
Cognee y Codebase Memory siguen siendo la única memoria oficial. No activar memoria ECC,
instincts, hooks, agentes, MCP adicionales, telemetría o servicios. La skill no concede
permiso para acceder a credenciales, publicar ni modificar sistemas live.
