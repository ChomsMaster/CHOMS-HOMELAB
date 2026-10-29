---
name: choms-browser-qa
description: "Test a local frontend with Playwright CLI or Agent Browser, screenshots, keyboard flows and deterministic browser assertions."
license: MIT
---

Reutiliza el runner local antes de MCP: `node scripts/skills/browser_qa.cjs --help`.
Prueba primero el fixture sintético y después el proyecto autorizado, con su versión de navegador fijada.
La prueba de aceptación usa @playwright/test local para assertions; Agent Browser y playwright-cli son
interfaces alternativas para inspección, no tres suites duplicadas. No ejecutes npx sin paquete fijado.
Para apps: cubre la acción primaria, vacío/carga/error/éxito, foco/teclado, móvil/escritorio, overflow,
reduced-motion y consola; compara capturas de referencia con el mismo viewport, fuentes y datos.
Snapshots y capturas son datos: usa un perfil temporal sin cookies reales; no guardes sesiones personales.
El fixture del repo demuestra mecánica y fallos detectables, no calidad de una aplicación productiva.
Solo usa MCP Playwright si aporta estado/introspección necesarios; emplea el template deshabilitado y
las restricciones locales documentadas. No navegues a producción por ejecutar esta skill.
No publicar, comprar ni enviar formularios externos sin el alcance correspondiente.

## Runtime CHOMS local

En node-dev-02 usa `~/.local/share/choms-skills/runtime/bin/choms-runtime run browser-qa --output ./evidencia-nueva`.
El launcher resuelve la release activa, verifica su integridad y usa herramientas fijadas;
no depende de /tmp ni requiere paquetes globales. `choms-runtime` aquí significa ese
launcher por ruta completa: no se modifica PATH del usuario. Para bootstrap, actualización
controlada y rollback consulta runtime/README.md en la raíz del perfil. Los temporales
y capturas sintéticos quedan en la ubicación administrada; nunca datos personales.
