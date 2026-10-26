---
name: choms-context-budget
description: "Reduce context overhead in large tasks, broad repositories or long sessions, and when asked to reduce consumption, while retaining evidence needed for safety and accuracy."
license: MIT
metadata:
  origin: CHOMS
  authorship: original
---

# Presupuesto de contexto

## Inspección y selección
- Empieza por búsquedas dirigidas, metadatos, estructura y diff para delimitar la pregunta.
  Carga solo archivos relevantes y los documentos obligatorios del proyecto; evita auditorías generales.
- Prefiere fragmentos con archivo/línea y resúmenes trazables a lecturas completas repetidas.
  Amplía el fragmento cuando no baste para entender contratos, errores o dependencias.
- Reutiliza evidencia ya obtenida si sigue vigente; evita duplicar contenido o cargar contexto ajeno.
  Si el archivo o estado cambió, vuelve a verificar la parte afectada.
- Consulta Codebase Memory solo cuando aporte historia, arquitectura o relaciones necesarias.
  Comprueba fuente y vigencia; no consultes por rutina ni conviertas el índice en verdad live.

## Checkpoints y exactitud
Antes de compactar o cambiar de fase, deja un checkpoint breve en el canal de trabajo autorizado:
objetivo, restricciones, decisiones, archivos/commits relevantes, checks completados, incertidumbres
y siguiente paso. No crees archivos de memoria ni incluyas secretos o transcripciones completas.

Nunca elimines evidencia necesaria para seguridad, exactitud o diagnóstico con el fin de ahorrar.
Distingue resúmenes de fuentes originales y recupera el detalle cuando una decisión dependa de él.
No inventes presupuestos, tokens ahorrados ni porcentajes: solo informa mediciones disponibles.
Esta skill selecciona qué contexto cargar; la estrategia de caché organiza el contenido repetido.

## Límites del perfil CHOMS
Cognee y Codebase Memory siguen siendo la única memoria oficial. No activar memoria ECC,
instincts, hooks, agentes, MCP adicionales, telemetría o servicios. La skill no concede
permiso para acceder a credenciales, publicar ni modificar sistemas live.
