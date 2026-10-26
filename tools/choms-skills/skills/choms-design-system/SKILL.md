---
name: choms-design-system
description: "Extract or audit design tokens, component consistency and accessible UI states in an authorized frontend codebase."
license: MIT
metadata:
  upstream: affaan-m/ECC
  upstream-tag: v2.2.3
  upstream-commit: c05b2d6614f62f6db0047669aa4eefb223d478f9
  upstream-skill: design-system
  adaptation: CHOMS isolated review candidate
---

# Sistema de diseño
Inspecciona solo las superficies autorizadas de CSS, Tailwind o componentes. Extrae colores,
tipografía, escala de espacio, radios, sombras y breakpoints; identifica consistencias y excepciones.
En modo generación propone tokens JSON, custom properties, DESIGN.md y preview HTML autocontenido.
Escribe esos artefactos solo dentro del trabajo solicitado. En modo auditoría entrega ejemplos
con archivo/línea para contraste, foco, jerarquía, responsive, estados vacíos y dark mode.
La investigación de competidores es opcional y usa únicamente navegador ya disponible/autorizado;
si no existe, declara la limitación. No instalar browser MCP ni dependencias.

## Límites del perfil CHOMS
Cognee y Codebase Memory siguen siendo la única memoria oficial. No activar memoria ECC,
instincts, hooks, agentes, MCP adicionales, telemetría o servicios. La skill no concede
permiso para acceder a credenciales, publicar ni modificar sistemas live.
