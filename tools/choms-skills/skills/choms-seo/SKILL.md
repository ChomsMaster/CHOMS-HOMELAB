---
name: choms-seo
description: "Review public website crawlability, metadata, structured data, performance and internal linking using page-specific evidence."
license: MIT
metadata:
  upstream: affaan-m/ECC
  upstream-tag: v2.2.3
  upstream-commit: c05b2d6614f62f6db0047669aa4eefb223d478f9
  upstream-skill: seo
  adaptation: CHOMS isolated review candidate
---

# SEO
Trabaja únicamente sobre páginas destinadas a ser públicas. Comprueba robots/noindex, canonical,
redirecciones, sitemap, hreflang si aplica y profundidad de enlaces. No conviertas dashboards
privados o endpoints administrativos en páginas indexables.
Después revisa intención por URL, título/descripción legibles, jerarquía de headings y enlaces descriptivos.
El marcado estructurado debe representar contenido visible real. Usa métricas de rendimiento observadas
cuando existan y separa mediciones de recomendaciones. No prometas rankings ni inventes métricas.
Cada hallazgo incluye URL o archivo, evidencia, impacto y corrección concreta. No añadir agentes,
servicios de analítica, APIs de keywords ni publicar cambios fuera del alcance autorizado.

## Límites del perfil CHOMS
Cognee y Codebase Memory siguen siendo la única memoria oficial. No activar memoria ECC,
instincts, hooks, agentes, MCP adicionales, telemetría o servicios. La skill no concede
permiso para acceder a credenciales, publicar ni modificar sistemas live.
