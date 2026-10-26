---
name: choms-prompt-caching-strategy
description: "Organize repeated prompts and shared instructions into stable and variable content for Codex or Hermes, without assuming cache availability or changing provider settings."
license: MIT
metadata:
  origin: CHOMS
  authorship: original
---

# Estrategia de prompt caching

## Contenido estable y variable
- Separa instrucciones/reglas/referencias estables de la petición actual, resultados de herramientas,
  estado del worktree y demás datos variables. Dentro de cada nivel de prioridad, mantén el bloque
  estable en un orden determinista; no reordenes instrucciones si cambia su significado o precedencia.
- Mantén timestamps, IDs aleatorios, métricas live y detalles de ejecución fuera del bloque estable.
  No elimines datos variables necesarios: inclúyelos en la parte correspondiente.
- Referencia archivos, versiones, commits o hashes comprobados en vez de repetir contenido grande.
  Una referencia no carga por sí sola un archivo: conserva el fragmento necesario si el runtime
  no puede recuperarlo o si la seguridad/exactitud exige evidencia directa.
- Si cambia una referencia o instrucción, actualiza su versión/hash; no reutilices contexto obsoleto
  para mantener un prefijo. No añadas secretos, credenciales, cookies ni payloads sensibles a material
  cacheable; usa únicamente referencias no sensibles cuando proceda.

## Independencia de la caché
La respuesta y los checks deben ser correctos con o sin caché. No afirmes que hay cache hit,
ahorro, latencia o retención sin evidencia del runtime. No crees una caché, almacén de memoria
ni sistema de persistencia adicional.

No inventes parámetros de proveedor ni modifiques modelos, configuración, OAuth o SDKs.
Aplica estas decisiones al contenido que controlas dentro del encargo; no alteres el formato
interno de Codex/Hermes. No realices llamadas de pago o inferencias para intentar forzar hits.
Esta skill organiza contenido estable; context-budget decide qué merece cargarse.

## Límites del perfil CHOMS
Cognee y Codebase Memory siguen siendo la única memoria oficial. No activar memoria ECC,
instincts, hooks, agentes, MCP adicionales, telemetría o servicios. La skill no concede
permiso para acceder a credenciales, publicar ni modificar sistemas live.
