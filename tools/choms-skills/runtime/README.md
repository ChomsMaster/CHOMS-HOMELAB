# Runtime CHOMS Skills 1.5.0

Runtime local de usuario en `~/.local/share/choms-skills/runtime`, Linux x86_64.
Requiere Python >=3.12 del host; se verifica en node-dev-02 con Python 3.14.4.
No instala paquetes del sistema, modifica PATH del usuario, configura servicios ni
accede a credenciales. El checkout canónico debe conservar su ubicación: el launcher
apunta al controlador versionado, como los enlaces de skills existentes.

## Versiones y procedencia

| Herramienta | Versión fijada |
|---|---|
| Node | v24.22.2, archivo oficial linux-x64 |
| Playwright CLI | 0.1.22 |
| Playwright MCP | 0.0.83 |
| Agent Browser | 0.41.0 |
| Chromium para CLI/MCP | Chrome for Testing 155.0.8059.12, revisión 1247 |
| Chromium para browser-QA | Headless Shell 156.0.8078.4, revisión 1248 |
| Suite QA | @playwright/test 1.64.1 |
| FFmpeg y ffprobe | 7.0.2-static; distribuidor eugeneware, release b6.1.1 |
| Gitleaks | 8.30.1 |
| PyYAML | 6.0.3, fuente Python pura sin compilación |

[RUNTIME.lock.json](RUNTIME.lock.json) fija URLs, SHA-256 de siete artefactos,
SHA-256 de helpers/fixtures/avisos y hashes del package.json/package-lock.json.
El lock npm existente fija las ocho entradas transitivas y su integridad SHA-512.
No cambian versiones de herramientas respecto al runtime validado anterior.
La etiqueta b6.1.1 del distribuidor no se confunde con la versión real 7.0.2 del binario.
No se atribuyen firmas independientes a los archivos Chrome; los hashes se fijaron
al descargarlos del origen primario y se verifican antes de cada extracción.
Avisos/licencias incluidos en los artefactos y snapshots locales; no se versionan
binarios o navegadores en Git ni se redistribuye contenido excluido por licencia.

## Bootstrap reproducible

Desde la raíz del checkout en la rama autorizada:

```sh
python3 scripts/skills/runtime.py bootstrap
```

Descarga únicamente URLs fijas, verifica cada digest antes de extraer e instala
los tarballs npm sin ejecutar lifecycle scripts ni resolver versiones con npm.
No requiere Node global. Lanza un Chromium vacío antes del sellado para comprobar
las dependencias del host; registra el marcador vacío de Playwright en el manifiesto.
No instala dependencias del sistema si faltan: falla sin activar la candidata.
Después ejecuta la aceptación completa y activa solo con un recibo PASS válido.
No hay inferencias ni tráfico a producción.

Con caché completa, reconstrucción/aceptación sin red:

```sh
python3 scripts/skills/runtime.py bootstrap --offline
```

La receta es de contenido: ID = primeros 32 caracteres del SHA-256 del lock exacto.
Una release existente se verifica; no se reconstruye silenciosamente encima de ella.
Un fallo conserva la etapa bajo releases/.stage-* para diagnóstico y deja current
sin cambios. Los únicos archivos del host que necesita son Python/bibliotecas del
sistema ya disponibles y este checkout; no hay dependencias operativas de /tmp.

## Ubicación e integridad

- downloads/: caché de artefactos nombrados por su digest; nunca ejecutada directamente.
- releases/ID/: herramientas y snapshots de helpers/fixtures; el gestor no los modifica después del sellado.
- seals/: hash del manifiesto y del lock por release.
- receipts/: aceptación de procesos nuevos vinculada al manifiesto exacto.
- current y previous: enlaces relativos con sustitución atómica y exclusión mutua.
- work/ y sockets/: datos sintéticos, capturas, temporales y cachés de ejecución.
- bin/choms-runtime: enlace reversible al controlador de este checkout.

El manifiesto incluye SHA-256 de archivos, permisos y destinos de symlinks; rechaza
archivos nuevos, eliminados, modificados y enlaces externos. Cada `run` verifica
el árbol completo y fija las rutas de esa release para el proceso. Una promoción
no altera los procesos ya abiertos ni mantiene el lock mientras un MCP atiende.
El sellado detecta deriva/corrupción; es estado del mismo usuario, no una firma
independiente ni aislamiento ante un usuario comprometido.

El runtime-v1 previo permanece intacto para Hermes y su evidencia histórica.
Figma OAuth/configuración y sus almacenes de credenciales no se usan ni migran.

## Uso desde procesos nuevos

Usar la ruta completa, sin depender de una modificación del PATH de la sesión:

```sh
~/.local/share/choms-skills/runtime/bin/choms-runtime status
~/.local/share/choms-skills/runtime/bin/choms-runtime verify
~/.local/share/choms-skills/runtime/bin/choms-runtime run node --version
~/.local/share/choms-skills/runtime/bin/choms-runtime run playwright-cli --version
~/.local/share/choms-skills/runtime/bin/choms-runtime run agent-browser --version
~/.local/share/choms-skills/runtime/bin/choms-runtime run validate-profile
~/.local/share/choms-skills/runtime/bin/choms-runtime run local-tools brief tools/choms-skills/fixtures/design-brief.json
~/.local/share/choms-skills/runtime/bin/choms-runtime run local-tools export origen.mp4 ./salida-nueva.mp4 --width 640 --height 640
```

Se proporcionan también `browser-qa`, `cli-smoke`, `design-mcp`, `mcp-probe`,
`playwright-mcp`, `ffmpeg`, `ffprobe` y `gitleaks`. Stdout de los MCP contiene solo
protocolo. El paquete Playwright MCP usa stdio bajo demanda: no se registra en
clientes, expone puertos persistentes ni altera Figma.

```sh
~/.local/share/choms-skills/runtime/bin/choms-runtime test
```

Ejecuta, en procesos nuevos, brief/lint frontend, veinte assertions browser en
390/1440 px, ambos CLI contra un formulario loopback, MCP sobre about:blank,
MCP de brief con entrada válida/inválida y medición/exportación sintética de vídeo
con audio y fit-and-pad a 640x640. Los helpers y fixtures están congelados dentro
de la release. El validador de perfil recibe explícitamente el perfil del checkout.
No se confunde esa prueba sintética con una app real, WCAG o un diseño de Figma.

TMPDIR, cachés y sockets de los hijos apuntan a la ubicación administrada. Se usa
configuración vacía propia de Agent Browser, sin importar perfiles/cookies del usuario.
El host no admite el sandbox de Chromium: únicamente los fixtures locales emplean
la excepción explícita ya validada. El wrapper MCP conserva sandbox por defecto;
el test añade --no-sandbox para about:blank. La allowlist loopback no sustituye
un aislamiento de red para navegación no fiable.

## Actualización controlada y rollback

No hay actualizaciones automáticas ni búsqueda de latest. En una rama autorizada,
revisar versiones, fuente, licencias y hashes nuevos; cambiar los locks versionados
(y helpers si corresponde) antes de preparar. Mantener los locks npm coherentes.

```sh
python3 scripts/skills/runtime.py prepare --lock ruta/receta-revisada.json
python3 scripts/skills/runtime.py test --release ID_CANDIDATA
python3 scripts/skills/runtime.py activate --release ID_CANDIDATA
python3 scripts/skills/runtime.py rollback
```

prepare no cambia current. activate exige integridad y recibo de aceptación PASS
ligado al mismo manifiesto. Un re-test incompleto invalida el PASS anterior.
rollback verifica la release anterior y su recibo antes de intercambiar pointers;
no borra versiones, cachés ni datos del usuario. También permite volver a un ID
conocido mediante activate. No hay limpieza amplia, caducidad ni actualizaciones
por hooks. Para desactivar el launcher se puede retirar solo su enlace, tras
verificar su destino; no se elimina el runtime-v1 ni otros enlaces de skills.

La revisión 2 añade snapshots de licencia/procedencia a la revisión 1, sin cambiar
ningún paquete. Ambas se probaron para demostrar promoción y rollback reales.
[RUNTIME_VALIDATION.json](RUNTIME_VALIDATION.json) recoge IDs, hashes y resultados.
