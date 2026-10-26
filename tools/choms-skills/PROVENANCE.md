# Procedencia CHOMS Skills 1.0.0

Adaptaciones CHOMS de affaan-m/ECC, release v2.2.3, commit
`c05b2d6614f62f6db0047669aa4eefb223d478f9`.
Tag object: `93f9f6154d164ccb9f4dc38858a2bc2d5dcab222`.
Árbol Git: `ae3070ee183d0bae220745ec9120964e6b671175`.
Release y commit contrastados con la API oficial. GitHub informó firma válida;
no se afirma verificación local mediante un keyring de confianza.

PROFILE.json registra para cada skill el archivo fuente ECC, SHA-256 original,
SHA-256 de la adaptación preparada y SHA-256 canónico. UPSTREAM.lock.json fija
la fuente; SHA256SUMS cubre todos los archivos de este directorio salvo él mismo.

La única modificación de contenido frente al perfil revisado es el nombre
`choms-mcp-patterns` → `choms-mcp-server-patterns`, solicitado para la promoción.
La skill verification-loop se conserva sin activar bajo optional/.

Las adaptaciones eliminan ejemplos de secretos visibles, actualizaciones de
dependencias, comandos live y escáneres que imprimen valores sensibles. No son
copias oficiales sin cambios ni una instalación de ECC. Se conserva su licencia MIT.
No se redistribuyen el clon, candidatos descartados, instaladores, agentes,
hooks, MCP, Vault, instincts ni sistemas de memoria/aprendizaje de ECC.
Cognee + Codebase Memory siguen siendo la única memoria oficial CHOMS.
