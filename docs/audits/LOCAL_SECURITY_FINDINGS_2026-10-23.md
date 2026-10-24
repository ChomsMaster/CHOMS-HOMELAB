# Evidencia histórica de validación local

El bloque anterior se validó dos veces: los checks estáticos pasaron y Trivy
fue bloqueante. Esa es una fotografía histórica, no la política vigente.
El diseño de infraestructura externa de ese bloque fue retirado del checkout
por petición del propietario. No se reescribe el historial Git.

La política vigente mantiene Trivy informativo; el backlog actualizado agrupa
61 hallazgos de Kubernetes (1 CRITICAL, 60 HIGH) sin cambiar sus manifiestos.
Véase [SECURITY_BACKLOG.md](../SECURITY_BACKLOG.md) y la evidencia de la ejecución
única del encargo actual en [LOCAL_VALIDATION.md](../operations/LOCAL_VALIDATION.md).
