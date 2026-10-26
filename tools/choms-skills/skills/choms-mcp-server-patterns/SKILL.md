---
name: choms-mcp-server-patterns
description: "Design or debug MCP tools, response schemas, stdio framing and HTTP transport without installing additional servers."
license: MIT
metadata:
  upstream: affaan-m/ECC
  upstream-tag: v2.2.3
  upstream-commit: c05b2d6614f62f6db0047669aa4eefb223d478f9
  upstream-skill: mcp-server-patterns
  adaptation: CHOMS isolated review candidate
---

# Patrones MCP
Empieza por los contratos del servidor y SDK realmente instalados. Define herramientas, parámetros,
respuestas y errores estructurados; separa la lógica del transporte. En stdio, stdout contiene solo
mensajes de protocolo y los diagnósticos sanitizados van a stderr. En HTTP verifica el contrato
Streamable HTTP soportado por esa versión, sin asumir compatibilidad legacy.
Registra la forma real de respuestas sanitizadas antes de añadir assertions: un cliente puede
encapsular JSON textual en result o content. Distingue errores de transporte, protocolo y herramienta.
Verifica handshake, tools/list, herramienta exacta y consulta no destructiva con fixtures.
Para una acción con efectos, documenta autorización, idempotencia y límites de retry.
Consulta documentación oficial cuando haga falta, usando herramientas disponibles. No instalar Context7,
SDKs, servidores ni configurar credenciales como efecto secundario de esta skill.

## Límites del perfil CHOMS
Cognee y Codebase Memory siguen siendo la única memoria oficial. No activar memoria ECC,
instincts, hooks, agentes, MCP adicionales, telemetría o servicios. La skill no concede
permiso para acceder a credenciales, publicar ni modificar sistemas live.
