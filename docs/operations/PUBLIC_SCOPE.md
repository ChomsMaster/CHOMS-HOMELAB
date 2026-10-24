# Alcance del checkout público

Este árbol conserva la plataforma base y las capacidades multimedia genéricas.
Las extensiones específicas y sus registros originales se mantienen en un
repositorio Git hermano exclusivamente local, con rutas relativas y comprobantes
SHA-256. La documentación de planificación detallada también se conserva allí.
No existe dependencia de esos archivos privados para las comprobaciones públicas.

Las cifras de inventarios fechados describen la plataforma completa observada
entonces; el alcance declarativo público actual es menor. Retirar código de este
checkout no cambia recursos runtime ni equivale a corregir hallazgos de seguridad.
El backlog distingue el riesgo aceptado del controlador MetalLB de los controles
pendientes; su manifiesto no se ha cambiado en esta separación.

Validación acotada sin red ni acceso a servicios:

```bash
./scripts/validate.sh --local-changes
```

Este modo analiza YAML y Python, sintaxis Bash, ShellCheck de líneas afectadas y contratos de políticas afectadas
y coherencia de namespaces, y escanea código cambiado con Gitleaks redactado.
No ejecuta aplicaciones ni scripts operativos; no invoca herramientas de clúster,
charts o infraestructura ni descarga schemas. Los contratos estructurales no
sustituyen validación completa de schemas ni una prueba de conectividad.

La validación completa existente sigue disponible para otro contexto autorizado.
La separación no autoriza publicación, commits ni reescritura de historia.


En modo acotado, los avisos heredados de ShellCheck en líneas no modificadas
se registran como informativos; los nuevos sí bloquean. Se revisan los contratos
de los archivos de políticas modificados y la coherencia global de namespaces,
sin convertir una separación de alcance en hardening de componentes ajenos.
La pasada inicial detectó avisos heredados y un espacio final; se corrigió el
espacio y se acotó el validador después. No se repitió la validación: los últimos
ajustes quedan pendientes de una nueva ejecución que autorice el propietario.
