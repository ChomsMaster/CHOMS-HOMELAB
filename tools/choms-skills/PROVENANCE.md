# Procedencia CHOMS Skills 1.1.0

El perfil conserva las adaptaciones CHOMS de affaan-m/ECC, release v2.2.3, commit
`c05b2d6614f62f6db0047669aa4eefb223d478f9`.
Tag object: `93f9f6154d164ccb9f4dc38858a2bc2d5dcab222`.
Árbol Git: `ae3070ee183d0bae220745ec9120964e6b671175`.
Release y commit contrastados con la API oficial. GitHub informó firma válida;
no se afirma verificación local mediante un keyring de confianza.

Para las entradas derivadas, PROFILE.json registra el archivo fuente ECC, SHA-256 original,
SHA-256 de la adaptación preparada y SHA-256 canónico. UPSTREAM.lock.json fija
la fuente; SHA256SUMS cubre todos los archivos de este directorio salvo él mismo.

En la promoción 1.0.0, la única modificación frente al perfil revisado fue el nombre
`choms-mcp-patterns` → `choms-mcp-server-patterns`, solicitado para la promoción.
La skill verification-loop se conserva sin activar bajo optional/.

Las adaptaciones eliminan ejemplos de secretos visibles, actualizaciones de
dependencias, comandos live y escáneres que imprimen valores sensibles. No son
copias oficiales sin cambios ni una instalación de ECC. Se conserva su licencia MIT.
No se redistribuyen el clon, candidatos descartados, instaladores, agentes,
hooks, MCP, Vault, instincts ni sistemas de memoria/aprendizaje de ECC.
Cognee + Codebase Memory siguen siendo la única memoria oficial CHOMS.

## Obras originales CHOMS — perfil 1.1.0

choms-context-budget y choms-prompt-caching-strategy se redactaron a partir de
los requisitos del operador; no son copias o adaptaciones de las skills ECC de
contexto/costes, no tienen un commit upstream externo y no heredan esos ejemplos.
Su origen se distingue por entrada en PROFILE.json y sus SHA-256 canónicos se
incluyen también en SHA256SUMS. Se distribuyen bajo MIT junto al perfil.
Las seis skills activas previas y verification-loop opcional no cambian.
La nueva versión no activa memoria, hooks, agentes, MCP ni aprendizaje.

## Obra original CHOMS — perfil 1.2.0

choms-memory-governance nace de los requisitos del operador del 27-10-2026.
Skill, esquema/política y helper sintético son código original MIT; no proceden
de memoria, hooks, agentes o aprendizaje ECC. Las ocho skills previas no cambian.
Los esquemas MCP observados se conservan como evidencia de tools/list, sin
invocar mutaciones ni afirmar escritura central. SHA256SUMS cubre todos los
archivos canónicos, incluidos referencias/helper y los recibos de descubrimiento.

## Integración original CHOMS — perfil 1.3.0

Se conecta únicamente la gobernanza original al MCP choms-memory autenticado,
tras E2E sintético Codex/Hermes, CAS y purga con reinicio. No cambia código ECC
ni las otras ocho skills. La persistencia real continúa bloqueada por backups;
la cola de prueba no es un fallback. No se activan captura, hooks ni aprendizaje.
