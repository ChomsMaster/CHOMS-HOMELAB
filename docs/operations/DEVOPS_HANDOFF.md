# Entrega local de recuperación y revisión

Rama feature/devops-hardening, sin push. Sustituido el diseño cloud previo por
un kit privado cifrado de configuración y un runbook de reconstrucción. No se
ha accedido a producción, secretos, kubeconfig ni estado. El exportador offline
no se ejecutó; tampoco git filter-repo ni migraciones de archivos de ocio.

- [Kit y contrato de entradas](RECOVERY_KIT.md): SOPS + age, allowlist cerrada,
  clave externa obligatoria, publicación atómica de ciphertext en repo hermano.
- [Reconstrucción](REBUILD_RUNBOOK.md): Ansible → K3s/datastore → ownership
  Terraform/Helm → manifiestos → reconciliación Secrets → verificación; incluye
  bootstrap previo de credenciales cuando una reconstrucción vacía lo exige.
- [Backlog](../SECURITY_BACKLOG.md): CRITICAL primero; Trivy informativo.
- [Alcance público](PUBLIC_SCOPE.md): separación local verificada, sin cambios
  de runtime ni publicación. El plan detallado se conserva fuera de este árbol.
- [Validación](LOCAL_VALIDATION.md): una ejecución estática final, sin exportación.

No hay copia de datos de aplicaciones en el kit. Recuperar la plataforma con
sus datos depende de los backups/volúmenes y de una prueba aislada pendiente.


## Resultado de la ejecución única

Ejecutado scripts/validate.sh una sola vez tras los cambios: **exit 0**,
failures=0, omissions=0. PASS: yamllint, seis Helm lint, Bash/ShellCheck,
Terraform fmt/validate del root homelab y Gitleaks. kubeconform general:
222 válidos, 35 sin schema omitidos; NetworkPolicies 126 válidas, sin omisiones.
Trivy informativo: 61 hallazgos (1 CRITICAL/60 HIGH), no bloqueante.
El exportador solo se analizó como código; no se ejecutó ni se probó cifrado/
descifrado con claves reales. Tampoco se creó/leyó el repositorio privado,
se accedió a producción, se restauraron datos o se ejecutó filter-repo.
