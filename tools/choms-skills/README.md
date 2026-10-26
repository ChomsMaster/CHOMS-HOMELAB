# CHOMS Skills

Perfil 1.0.0, adaptado de ECC v2.2.3 y fijado por commit y SHA-256.
Solo instrucciones Markdown: sin ejecutables, hooks, servicios ni MCP nuevos.

## Selección activa

- choms-frontend-direction
- choms-design-system
- choms-seo
- choms-mcp-server-patterns
- choms-security-review
- choms-kubernetes-patterns

`optional/choms-verification-loop` queda fuera de las raíces enlazadas.

## Activación nativa

En node-dev-01 se resolvieron las raíces nativas: Codex `~/.agents/skills`
y Hermes `~/.hermes/skills`. Se enlaza cada uno de los seis directorios de
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
Para desactivar, retirar únicamente los seis enlaces después de verificar
que cada uno sigue apuntando a esta copia canónica. No borrar sus destinos,
la memoria, configuraciones, skills ajenas o credenciales. Recargar el catálogo
o reiniciar la sesión si el runtime mantiene una caché previa.
