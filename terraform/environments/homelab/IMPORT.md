# Adopción de recursos existentes (operador; NO ejecutado)

Este root adopta 13 namespaces públicos y seis releases del inventario de
23-10-2026. Los cuatro namespaces del sistema/default conservan ownership K3s.
No se gestionan Secrets, PVs, PVCs ni workloads directos desde Terraform.
Los values se leen sin modificación desde los archivos existentes, en el mismo
orden que el instalador Helm. Versions/chart namespace provienen de releases.json.

## Barrera de ownership

**No ejecutar apply antes de importar todo y revisar el plan.** No usar a la vez
el instalador Helm histórico y Terraform como escritores. Elegir Terraform solo
tras aceptación de los imports. Un import lee el cluster y escribe estado local;
NO se realizó en esta tarea. Helm puede persistir valores/metadata sensibles en
estado aunque el código solo use referencias: tratar todo estado como secreto.
`prevent_destroy` evita destrucciones declaradas, no evita cambios de values.
La versión de chart no asegura igualdad de values efectivos ni cero rollouts.
No usar `ignore_changes = all` para esconder drift.

## Secuencia exacta para el operador

1. Archivar de forma privada el estado si existe y definir custodia/locking.
2. Preparar autenticación por el mecanismo de entorno de los providers fuera
   del repo. No guardar tokens en tfvars ni argumentos shell; no exportar ni
   imprimir kubeconfig. Comprobar las opciones de autenticación de ambos providers
   (Helm 2.17 y Kubernetes 2.38) con las versiones bloqueadas.
3. Establecer `TF_VAR_cluster_endpoint` con el endpoint real no sensible. El valor
   por defecto es loopback inerte para evitar un destino implícito de producción.
4. En una tarea operacional autorizada distinta ejecutar desde este directorio:

```bash
terraform init
terraform import 'kubernetes_namespace_v1.platform["apps"]' 'apps'
terraform import 'kubernetes_namespace_v1.platform["cert-manager"]' 'cert-manager'
terraform import 'kubernetes_namespace_v1.platform["colegio-maria-rosario-staging"]' 'colegio-maria-rosario-staging'
terraform import 'kubernetes_namespace_v1.platform["databases"]' 'databases'
terraform import 'kubernetes_namespace_v1.platform["diagnostics"]' 'diagnostics'
terraform import 'kubernetes_namespace_v1.platform["filebrowser"]' 'filebrowser'
terraform import 'kubernetes_namespace_v1.platform["logging"]' 'logging'
terraform import 'kubernetes_namespace_v1.platform["media"]' 'media'
terraform import 'kubernetes_namespace_v1.platform["metallb-system"]' 'metallb-system'
terraform import 'kubernetes_namespace_v1.platform["monitoring"]' 'monitoring'
terraform import 'kubernetes_namespace_v1.platform["nfs-provisioner"]' 'nfs-provisioner'
terraform import 'kubernetes_namespace_v1.platform["security"]' 'security'
terraform import 'kubernetes_namespace_v1.platform["traefik"]' 'traefik'
terraform import 'helm_release.platform["choms-nfs"]' 'nfs-provisioner/choms-nfs'
terraform import 'helm_release.platform["cert-manager"]' 'cert-manager/cert-manager'
terraform import 'helm_release.platform["traefik-k8s"]' 'traefik/traefik-k8s'
terraform import 'helm_release.platform["choms-monitoring"]' 'monitoring/choms-monitoring'
terraform import 'helm_release.platform["choms-loki"]' 'logging/choms-loki'
terraform import 'helm_release.platform["choms-alloy"]' 'logging/choms-alloy'
```

5. Revisar `terraform plan` de forma privada. **Estos comandos de plan/import no
   fueron ejecutados aquí.** Resolver diferencias de metadata, configuración
   importada y values antes de autorizar cualquier apply. Mantener las releases
   existentes; no importar recursos con el mismo nombre en namespaces distintos.
6. Solo después de revisión, adoptar mediante el procedimiento de cambios del
   propietario. Probar salud y rollback por release. Registrar ownership.

## Backend

Sin bloque backend Terraform usa backend local por defecto (`terraform.tfstate`).
Los patrones de estado, planes, `.terraform/` y tfvars privados están ignorados.
Gitignore no cifra ni elimina ficheros ya publicados. Nunca subir ni mostrar estado.
Para validar, `scripts/validate.sh` copia únicamente código a una carpeta temporal,
usa `terraform init -backend=false` para descargar providers públicos, y ejecuta
`terraform validate`; no lee ningún estado existente ni configura backend real.

El backend sigue local. Una futura migración a backend remoto requiere diseño
separado de cifrado, locking, permisos y recuperación; no se declara ningún
backend remoto en este encargo. Nunca copiar estado al kit de recuperación.

Los providers están fijados por versión. Los lockfiles/checksums se generan en el
scratch de validación, no se adoptan como lockfile del repo todavía: generar y
revisar `.terraform.lock.hcl` en una tarea de dependencias, sin backend real,
antes de adopción. Falta pin por hashes revisados de los providers.
