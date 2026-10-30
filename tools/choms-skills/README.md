# CHOMS Skills

Perfil 1.5.0: seis adaptaciones de ECC v2.2.3 y tres skills originales CHOMS,
con procedencia y SHA-256 por entrada. Añade cuatro módulos locales,
activados en node-dev-02 para Codex y Hermes; [estado, uso y bloqueos](NEXT.md).
Instrucciones y un helper Python stdlib para pruebas sintéticas de gobernanza;
sin hooks ni captura automática. Gobernanza usa el MCP independiente choms-memory;
E2E central sintético acreditado, memorias reales bloqueadas por gate de backups.

## Selección activa

- choms-frontend-direction
- choms-design-system
- choms-seo
- choms-mcp-server-patterns
- choms-security-review
- choms-kubernetes-patterns
- choms-context-budget
- choms-prompt-caching-strategy
- choms-memory-governance

`optional/choms-verification-loop` queda fuera de las raíces enlazadas.

## Activación nativa

En node-dev-01 se resolvieron las raíces nativas: Codex `~/.agents/skills`
y Hermes `~/.hermes/skills`. Se enlaza cada uno de los nueve directorios de
skills/ por separado, tras comprobar colisiones por ruta y nombre. No enlazar
este directorio completo: incluiría optional/ en un escaneo recursivo.

Codex descubre skills mediante skills/list del app-server sin iniciar turnos.
Hermes usa su catálogo y carga explícita `/choms-<nombre>`; sus funciones nativas
permiten comprobar listado y lectura sin inferencia. El toolset actual de Hermes
se conserva: no se habilita el bundle skills porque también expone skill_manage.
No se activan creación automática, aprendizaje ni mantenimiento autónomo.
No se inicia gateway, daemon ni modelo para validar este perfil.

Los enlaces apuntan al checkout canónico: una actualización Git modifica la
skill enlazada. Revisar los cambios de skills antes de aceptar nuevas versiones.
En otro equipo, resolver las raíces del runtime de nuevo y comprobar colisiones;
no asumir rutas ni sobrescribir archivos existentes.

## Integridad y rollback

Desde este directorio: `sha256sum -c SHA256SUMS`.
PROFILE.json y [PROVENANCE.md](PROVENANCE.md) conservan fuente, licencia y hashes.
No promover optional/ ni copiar configuración ECC.
Para desactivar, retirar únicamente los nueve enlaces después de verificar
que cada uno sigue apuntando a esta copia canónica. No borrar sus destinos,
la memoria, configuraciones, skills ajenas o credenciales. Recargar el catálogo
o reiniciar la sesión si el runtime mantiene una caché previa.

## Contexto y prompts

context-budget acota lecturas y checkpoints sin sacrificar evidencia.
prompt-caching-strategy separa contenido estable/variable sin asumir una caché
real, alterar proveedores o prometer ahorro. Ambas son instrucciones portables
para Codex y Hermes, sin scripts ni dependencias adicionales.

## Gobernanza v1

La nueva skill aplica consentimiento, clasificación, conflictos, olvido y checkpoints.
Consulta su política/esquema solo cuando corresponda. El MCP choms-memory ofrece
ocho operaciones autenticadas, E2E sintético y purga acreditados desde ambos clientes.
La allowlist de choms-codebase-memory permanece intacta. Memorias reales bloqueadas
por el gate de backups; el helper local solo escribe fixtures en mktemp, nunca
datos reales ni Cognee, y no es otra memoria oficial.
Validador: `python3 scripts/skills/validate_profile.py` desde la raíz del repo.
Pruebas: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/tests -p test_memory_governance.py`.

Runtime administrado y bootstrap reproducible: [runtime/README.md](runtime/README.md).
Las herramientas se encuentran por el launcher de usuario, con integridad y rollback;
las nueve skills canónicas y Figma permanecen intactos.
