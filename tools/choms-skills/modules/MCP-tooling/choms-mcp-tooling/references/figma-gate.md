# Figma: preparado hasta autenticación

Fuente oficial: https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/
Endpoint oficial https://mcp.figma.com/mcp; autenticación OAuth real del usuario necesaria.
`config/figma.codex.toml` y `config/figma.hermes.yaml` están deshabilitados y no contienen secretos.
No se mezclan con la configuración del usuario. Revisa soporte del cliente antes de activarlos.

El operador habilita la entrada en su cliente y realiza OAuth en el navegador del proveedor.
Detenerse en ese gate: no solicitar tokens por chat, copiar sesiones o guardar credenciales en Git.
Después: initialize, tools/list y lectura de un nodo explícitamente autorizado, comparación con captura,
y evidencia agregada. No invocar escritura al canvas. MCP remoto cambia sin digest local: conservar fecha,
versión negociada y nombres de tools observados; no declarar un hash de servidor inventado.

Playwright MCP: config/playwright.mcp.json usa el paquete local bloqueado, stdio, headless, isolated,
bind loopback y allowed-origins local. Estas opciones reducen exposición, no son sandbox de seguridad.
Ejecutar únicamente fixtures locales y cerrar el proceso. Credenciales y storage-state fuera del perfil.
