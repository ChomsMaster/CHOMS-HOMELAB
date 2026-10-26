# Overlay wreq-js — aplicado y validado

Procedencia exclusiva: repositorio oficial diegosouzapw/OmniRoute, tag v3.8.52,
commit `ad6f33f66bda34eba98645d3bfdabbde294bc843` (checkout limpio).
Los dos chunks compilados se leyeron de la imagen oficial principal fijada en
`provenance.json`. No se afirma que sus bytes sean reproducibles compilando el
TypeScript: se preservan íntegros salvo una sustitución exacta por chunk.
La licencia MIT upstream se conserva en LICENSE.

## Cambio mínimo

La fuente `open-sse/executors/codex.ts` usa `createRequire(import.meta.url)` y
`codex/wreqLoader.ts` usa `Reflect.apply(requireFn, undefined, [moduleName])`.
En los chunks publicados, los módulos 379401 y 506208 son contexts vacíos que
siempre lanzan MODULE_NOT_FOUND. Solo esos módulos se sustituyen por
`require("node:module").createRequire("/app/package.json")`: conserva resolución
nativa desde la raíz del paquete, sin instalar dependencias, fallback ni hooks.
Las cadenas antes/después, tamaños y SHA-256 están en `provenance.json`.
Reproducir cada artefacto requiere verificar el hash original, exigir una sola
coincidencia de `before`, sustituir por `after` y exigir el hash final. Nunca
aplicar la sustitución a otros archivos ni a otra versión de la imagen.

ConfigMap inmutable `omniroute-wreq-loader-43e57fc7bdb1`; solo las claves
1056.js y 34899.js se montan read-only/subPath en sus rutas exactas del
contenedor principal. No se monta el directorio completo. Imagen principal,
sidecar, OAuth, PVC, Services y rutas permanecen sin cambios en este hotfix.

## Validación offline

`offline-test.cjs <directorio>` recibe provenance.json y los dos archivos
extraídos del campo data del ConfigMap. Comprueba SHA/tamaño, reconstrucción
exacta del original, sintaxis de ambos chunks, fallo MODULE_NOT_FOUND original,
require nativo corregido, export websocket real de wreq-js y rechazo de módulo
ausente: 16/16 PASS. Ejecutado en la imagen runner-cli ya disponible, con
`--pull=never --network none --read-only --cap-drop ALL` y UID 1000; no inicia
OmniRoute ni app-server, no lee credenciales y no hace inferencias.
La prueba offline se complementó tras autorización con rollout 2/2 Ready, cero
reinicios, hashes montados exactos, ausencia de error de importación, WS,
initialize/account/read y proveedor valid=true. Una sola nueva solicitud
cxa/gpt-6-sol respondió HTTP 200 con PONG. No se alteraron los clientes.

## Procedimiento de aplicación/reaplicación controlada

Primero comprobar que los hashes live siguen siendo los originales del lock,
que el digest principal sigue fijado y que el diff solo añade este ConfigMap,
dos mounts y su volumen. Hacer dry-run servidor y diff de ambos objetos antes
de aplicar. Crear el ConfigMap antes de aplicar únicamente Deployment/omniroute
extraído de workloads.yaml; no reaplicar Redis ni recursos ajenos. El cambio de
PodSpec produce un rollout Recreate y una breve indisponibilidad de OmniRoute.
Aplicado con este procedimiento tras autorización. No usar un apply recursivo
del directorio para este cambio.

## Rollback

Retirar exclusivamente los dos mounts wreq-loader-hotfix del contenedor
principal y el volumen de ese nombre del Deployment preparado; conservar
sidecar, mounts CODEX_HOME/capability, configuración OAuth, PVC y Secrets.
Tras dry-run/diff, aplicar solo Deployment/omniroute y esperar Ready. Al recrear
el Pod reaparecen los chunks originales de la misma imagen inmutable. El
ConfigMap puede permanecer sin uso; no es necesario borrarlo. No usar undo a
una revisión anterior al sidecar ni revertir el diff preparado completo.

## Riesgos y pendientes

- Código vendorizado ligado a hashes de esta imagen; IDs/layout cambian con un
  rebuild o upgrade. Retirar/revisar el overlay antes de actualizar OmniRoute.
- Los mounts subPath no se actualizan en caliente; ConfigMap inmutable y nombre
  versionado evitan cambios silenciosos. Falta de clave impide el arranque.
- Protocolo y una respuesta PONG acreditados; no demuestra carga, todos los
  modelos ni comportamiento de herramientas en conversaciones completas.
- No modifica la política de seguridad ni corrige otras dependencias/CVEs.
- Backup/restore del CODEX_HOME y escaneo CVE quedan pendientes. Una futura
  actualización debe retirar o revalidar este overlay contra hashes nuevos.
