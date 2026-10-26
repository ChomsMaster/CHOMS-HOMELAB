---
name: choms-verification-loop
description: "Select and report the relevant existing verification gates for an authorized change without repeating already completed checks."
license: MIT
metadata:
  upstream: affaan-m/ECC
  upstream-tag: v2.2.3
  upstream-commit: c05b2d6614f62f6db0047669aa4eefb223d478f9
  upstream-skill: verification-loop
  adaptation: CHOMS isolated review candidate
---

# Verificación acotada
Lee el contrato de validación del proyecto y el alcance del diff. Reutiliza el validador existente
como fuente única: build, tipos, lint, tests, revisión sensible y diff solo donde correspondan.
No dupliques una suite aprobada ni crees hooks o verificaciones periódicas. Herramienta ausente es
SKIP con motivo, nunca PASS. No impongas un umbral de cobertura arbitrario al proyecto.
Conserva exit codes reales cuando recortes salida; evita pipelines que oculten el fallo o causen SIGPIPE.
Revisión sensible: resultado redactado, nunca líneas con posibles valores. Cada check tiene nombre,
comando, resultado y límites de evidencia; separa defecto nuevo, aviso heredado y no aplicable.
No corregir, instalar, commitear ni publicar automáticamente por activar esta skill.

## Límites del perfil CHOMS
Cognee y Codebase Memory siguen siendo la única memoria oficial. No activar memoria ECC,
instincts, hooks, agentes, MCP adicionales, telemetría o servicios. La skill no concede
permiso para acceder a credenciales, publicar ni modificar sistemas live.
