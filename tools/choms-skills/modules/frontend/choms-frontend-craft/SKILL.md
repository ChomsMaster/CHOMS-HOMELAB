---
name: choms-frontend-craft
description: "Refine frontend motion, turn a design brief or supplied image into code, and review UI details using local evidence."
license: MIT
---

Usa choms-frontend-direction y choms-design-system para dirección y tokens: no vuelvas a definirlos.
Antes de inferir, ejecuta búsqueda local de componentes y tokens; usa el brief original y los assets suministrados.
Completa el [contrato de diseño](references/design-contract.md) para Prompt de Diseño o Image to Code.
Emil/Impeccable/Taste aportan revisión de detalle: propósito de cada animación, respuesta inmediata,
interrupción, foco, teclado, táctil, texto largo y reduced-motion. Conserva el sistema elegido; ninguna
preferencia estética autoriza sustituir tipografías, stack o navegación. No instales el bundle upstream.
Para Image to Code inspecciona primero la imagen, mide viewport, regiones, tipografía, colores y estados;
reutiliza assets locales y compara capturas al mismo tamaño antes de pedir generación de imágenes.
Ejecuta el lint HTML local y las pruebas browser-QA; el lint estructural no acredita WCAG ni fidelidad visual.
Lee CANDIDATES.json solo para procedencia o búsqueda; awesome-design-md es inspiración, no identidad de marca.
La regla atribuida a Bercer y el prompt externo no tienen fuente inequívoca: no inventes una atribución.
Prioridad LOCAL-FIRST, DETERMINISTIC-FIRST, AI-LAST: infiere solo decisiones visuales que no resuelvan fuentes locales.

## Runtime CHOMS local

En node-dev-02 usa `~/.local/share/choms-skills/runtime/bin/choms-runtime run local-tools brief ruta/brief.json`.
El launcher resuelve la release activa, verifica su integridad y usa herramientas fijadas;
no depende de /tmp ni requiere paquetes globales. `choms-runtime` aquí significa ese
launcher por ruta completa: no se modifica PATH del usuario. Para bootstrap, actualización
controlada y rollback consulta runtime/README.md en la raíz del perfil. Los temporales
y capturas sintéticos quedan en la ubicación administrada; nunca datos personales.
