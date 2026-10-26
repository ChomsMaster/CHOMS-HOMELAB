---
name: choms-frontend-direction
description: "Choose product-specific typography, layout, color and interaction direction for frontend work, respecting the existing UI system."
license: MIT
metadata:
  upstream: affaan-m/ECC
  upstream-tag: v2.2.3
  upstream-commit: c05b2d6614f62f6db0047669aa4eefb223d478f9
  upstream-skill: frontend-design-direction
  adaptation: CHOMS isolated review candidate
---

# Dirección frontend
Antes de implementar identifica propósito, audiencia, tono, detalle visual distintivo y restricciones.
Distingue una herramienta operativa de una landing comercial: prioriza el flujo real en el primer viewport.
Reutiliza componentes, tokens e iconos existentes. Decide jerarquía, tipografía, espaciado, contraste,
responsive y estados antes de añadir decoración. Usa movimiento solo para explicar cambios de estado.
Comprueba textos largos, overflow y tamaños en móvil/escritorio con herramientas ya autorizadas.
No añadas dependencias ni servicios para conseguir un efecto visual. Si hay Product Design disponible,
coordina con ese flujo en lugar de ejecutar dos auditorías equivalentes.

## Límites del perfil CHOMS
Cognee y Codebase Memory siguen siendo la única memoria oficial. No activar memoria ECC,
instincts, hooks, agentes, MCP adicionales, telemetría o servicios. La skill no concede
permiso para acceder a credenciales, publicar ni modificar sistemas live.
