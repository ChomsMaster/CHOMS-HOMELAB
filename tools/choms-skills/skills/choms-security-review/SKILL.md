---
name: choms-security-review
description: "Review the authorized change for authentication, validation, secret leakage and least-privilege defects with evidence and proposed fixes."
license: MIT
metadata:
  upstream: affaan-m/ECC
  upstream-tag: v2.2.3
  upstream-commit: c05b2d6614f62f6db0047669aa4eefb223d478f9
  upstream-skill: security-review
  adaptation: CHOMS isolated review candidate
---

# Revisión de seguridad
Delimita el diff y las superficies de confianza. Revisa autenticación/autorización, validación de
entradas, consultas parametrizadas, XSS/CSRF según el modelo real de sesiones, rate limits,
subidas de archivos y mensajes de error. Comprueba referencias a secretos sin leer sus valores.
No copies credenciales, cookies o payloads en informes. Usa scanners existentes con salida redactada;
no uses grep que imprima líneas potencialmente sensibles. Distingue ejemplos ficticios de filtraciones
reales sin divulgar el contenido.
Revisa dependencias y permisos declarativos; propone cambios, sin npm audit fix/update ni rotación,
instalación, modificación de IAM o acciones destructivas automáticas.
Entrega severidad, archivo/línea, evidencia sanitizada, corrección y validación necesaria.
Declara lo no comprobado. Esta revisión no acredita por sí sola ausencia de vulnerabilidades.

## Límites del perfil CHOMS
Cognee y Codebase Memory siguen siendo la única memoria oficial. No activar memoria ECC,
instincts, hooks, agentes, MCP adicionales, telemetría o servicios. La skill no concede
permiso para acceder a credenciales, publicar ni modificar sistemas live.
