# Validación local y CI

Fuente única: `./scripts/validate.sh`, invocada también por CI. No ejecuta el
exportador de recuperación ni accede a producción o a entradas privadas.
Bash -n y ShellCheck analizan el exportador como código, nunca lo lanzan.

```bash
export PATH="$PWD/.cache/devops/bin:$PWD/.cache/devops/venv/bin:$PATH"
./scripts/validate.sh
```

Checks bloqueantes: yamllint, seis Helm lint con charts en caché y values reales,
kubeconform (incluida una pasada estricta para políticas estándar), bash -n
individual, ShellCheck, Terraform fmt/validate y Gitleaks redactado. Los schemas
no disponibles de CRDs/Gateway API se contabilizan como omitidos, no como válidos.
Terraform se valida solo en copias temporales del root homelab, con init
-backend=false, HOME temporal y entorno sin autenticación. No se copia estado,
kubeconfig, claves, tfvars ni inputs de recuperación. No hay plan ni apply.

**Trivy informativo:** se ejecuta sobre el snapshot de código, mantiene
HIGH/CRITICAL en diagnósticos saneados y no bloquea por hallazgos, error o ausencia.
Los demás fallos siguen bloqueando; otras herramientas/charts ausentes hacen
fallar CI por cobertura incompleta. El resultado se distingue de las advertencias.
Backlog: [SECURITY_BACKLOG.md](../SECURITY_BACKLOG.md). No es un hardening validado.

Pines existentes: actions por SHA, tools/charts/providers por versión. Faltan
hashes revisados de archives y providers, dependencias transitivas y schemas.
SOPS/age son dependencias manuales del exportador, no se instalan ni ejecutan
como parte de validación. Gitleaks no revisa el historial ni archivos privados.
La preparación opcional de herramientas públicas sigue en
scripts/prepare-validation-tools.sh; no requiere acceso al clúster.

## Ejecución del encargo actual

Una única ejecución al final de los cambios. Resultado registrado al cierre;
ninguna ejecución funcional del exportador ni prueba de restauración realizada.


## Resultado de la ejecución única

Ejecutado scripts/validate.sh una sola vez tras los cambios: **exit 0**,
failures=0, omissions=0. PASS: yamllint, seis Helm lint, Bash/ShellCheck,
Terraform fmt/validate del root homelab y Gitleaks. kubeconform general:
222 válidos, 35 sin schema omitidos; NetworkPolicies 126 válidas, sin omisiones.
Trivy informativo: 61 hallazgos (1 CRITICAL/60 HIGH), no bloqueante.
El exportador solo se analizó como código; no se ejecutó ni se probó cifrado/
descifrado con claves reales. Tampoco se creó/leyó el repositorio privado,
se accedió a producción, se restauraron datos o se ejecutó filter-repo.
