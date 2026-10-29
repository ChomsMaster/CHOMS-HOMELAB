---
name: choms-mcp-tooling
description: "Build and probe local MCP tool contracts, discover existing skills offline, and prepare Figma authentication without storing credentials."
license: MIT
---

Reutiliza choms-mcp-server-patterns para transporte y contratos. Este módulo añade ejecución local:
`python3 scripts/skills/local_tools.py find browser` busca en el catálogo versionado sin red ni instalación.
`python3 scripts/skills/mcp_probe.py -- python3 scripts/skills/design_mcp.py` prueba initialize,
notifications/initialized, tools/list, llamada válida e inválida y método desconocido sin modelos.
El servidor de ejemplo valida briefs en memoria: no lee archivos del cliente ni ofrece memoria persistente.
Al construir un MCP real, usa el SDK ya fijado por el proyecto, schemas cerrados, errores útiles,
readOnlyHint/destructiveHint correctos y stdout exclusivo del protocolo. El fixture no sustituye un SDK completo.
MCP Builder se solapa con la skill ECC existente: no añadas otro paquete con el mismo propósito.
Para Figma usa [configuración y gate](references/figma-gate.md): template preparado y sin tokens.
No extraigas credenciales de clientes existentes. No inicies OAuth ni escrituras Figma automáticamente.
Una vez que el operador autentique, prueba lista de tools y una lectura del nodo autorizado; no marques
conectado por disponer de un URL. El servidor remoto no ofrece un hash binario verificable localmente.
