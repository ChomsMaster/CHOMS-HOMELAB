# CHOMS Skills/MCP — integración y activación local 1.4.1

Preparado en `feat/skills-mcp-next` desde `69a2f4b`; integración en main
mediante merge trazable autorizada por el operador el 29-10-2026, sin despliegue.
Principio: LOCAL-FIRST, DETERMINISTIC-FIRST, AI-LAST. Cuatro módulos originales
MIT en modules/, activados en node-dev-02 mediante enlaces individuales. Las nueve skills canónicas y
verification-loop permanecen byte a byte intactas. ECC sigue fijado a v2.2.3;
no se instala su bundle, memoria, hooks ni proveedores.

## Estado exacto

| Capacidad | Resultado de este bloque |
|---|---|
| frontend | Módulo activado: complemento de dirección/sistema existentes; detalle Emil/Impeccable/Taste, contrato CHOMS, flujo Image to Code y lint HTML local |
| browser-QA | Módulo activado; runner real Chromium, CLI Playwright y Agent Browser probados con fixture local |
| MCP-tooling | Módulo activado; búsqueda offline, servidor stdio de validación de briefs y probe ejecutados |
| vídeo-social | Módulo activado; medición YUV por género, metadatos y exportación fit-and-pad locales probados; publicación OFF |
| MCP Playwright | Handshake, 25 tools, navegación about:blank y cierre PASS; template sin registrar |
| MCP Figma | OAuth acreditado en Codex, conexión persistente y reversible; 45 tools, whoami y rechazo de lectura sintética PASS. Sin lectura de diseños reales |
| Prompt de Diseño | **Identificación pendiente**, nombre original, no activado y no cubierto |
| Regla de Diseño de Bercer | **Identificación pendiente**, nombre original, no activada y no cubierta |
| web-design-guidelines | Fuente y hash revisados; licencia del repo no acreditada por archivo. Sin redistribuir instrucciones; lint/revisión CHOMS propios, sin afirmar conformidad completa |
| awesome-design-md | Referencia revisada con licencia MIT y commit/hash; no se copian marcas, assets ni DESIGN.md de terceros |

CANDIDATES.json distingue las quince entradas (Emil e Impeccable por separado),
solapamientos, fuentes, licencia y huecos. No se atribuye a los dos nombres pendientes
el contrato original CHOMS. El usuario confirma que no dispone de sus fuentes.
Taste audiovisual reutiliza el enfoque medido de ECC content-engine, video-editing,
taste-distillation y taste-application, sin importar sus scripts/pipelines.
No se implementan LUT perceptual, montaje por cadencia o generación de vídeo.

## Activación y alcance real

El perfil 1.3.0 documentaba nueve enlaces en node-dev-01. En node-dev-02 no había
enlaces CHOMS: se crearon 26 enlaces (13 por cliente), sin sobrescrituras, conservando
las nueve fuentes canónicas y añadiendo los cuatro módulos. verification-loop sigue
sin enlace. Codex descubre 13/13 desde la raíz de usuario real y se comprueba el
contenido completo de sus rutas. Hermes ejecuta skills_list, skill_view sin
preprocesamiento y build_skill_invocation_message: catálogo/lectura/slash 13/13.

Se usa el subsistema nativo de skills de Hermes en el commit fijado, persistido bajo
~/.local/share/choms-skills/runtime-v1/hermes; no se instala la interfaz de chat,
proveedores ni gateway. Su aviso sobre destinos de symlink fuera de la raíz de
skills se conserva: destinos exactos y hashes comprobados, sin relajar la confianza.
Plugins de autenticación opcionales sin httpx no se inicializan; no afectan las
funciones nativas de skills probadas. No se habilita skill_manage ni aprendizaje.

PROFILE.json declara la composición reuse_existing y activación de cada módulo.
ACTIVATION_VALIDATION.json es la evidencia actual. NEXT_VALIDATION.json y
DISCOVERY_VALIDATION.json conservan sus fases históricas sin reescritura.
Los comandos siguen ejecutándose desde la raíz del repositorio; no hay turnos de IA.

Reversión exacta, solo de los enlaces creados por esta promoción:
`python3 scripts/skills/activate_native.py --rollback --receipt ~/.local/share/choms-skills/activation-node-dev-02.json`.
El helper comprueba todas las colisiones antes de crear enlaces y todos los
destinos antes de retirar alguno; no sobrescribe paths ni elimina skill sources.

Verificación real desde raíces instaladas:
`PYTHONPATH=~/.local/share/choms-skills/runtime-v1/pydeps PYTHONDONTWRITEBYTECODE=1 python3 scripts/skills/verify_native_activation.py --hermes-source ~/.local/share/choms-skills/runtime-v1/hermes`.

Figma está conectado de forma persistente en Codex de node-dev-02 mediante la
entrada `mcp_servers.choms_figma` de `~/.codex/config.toml`, solo URL oficial y
enabled=true. OAuth completado por el operador y consumido exclusivamente por el
cliente nativo, sin extraer ni copiar tokens. Tres procesos nuevos conectaron
sin overrides de configuración ni nuevo login. [Evidencia Figma](FIGMA_VALIDATION.json).

El servidor declara Figma MCP Server 1.0.0, 45 herramientas (26 anotadas readOnlyHint),
121 recursos y capacidades tools/resources/prompts. Es una foto del servicio remoto,
no un digest de binario ni garantía de catálogo futuro. El catálogo se enumera en
la evidencia por nombre/anotaciones, sin contenido de usuario. No se ejecutan las
herramientas de escritura ni generación disponibles.

La lectura autenticada whoami {} devuelve éxito; identidad descartada sin imprimir.
get_metadata con fileKey CHOMSSYNTHETICFIXTURE0001/nodeId 0:0 devuelve isError=true,
rechazo esperado para el archivo inexistente. Esto acredita dispatch y rechazo
sintéticos, **no lectura de un diseño real**. No se crea una sesión remota Figma,
archivo, asset o fixture para conseguir una lectura positiva.

Para desactivar de forma persistente, cambiar **solo** enabled a false dentro de
esa entrada. Para retirar el registro, `codex mcp remove choms_figma`; no restaurar
configuraciones completas ni ejecutar logout como parte de esa reversión.
Se puede reponer la entrada con la misma URL y enabled=true; el cliente nativo
gestiona la vigencia OAuth y cualquier renovación necesaria, sin copiar credenciales.
Los templates de config/ siguen inertes para otros equipos. Hermes no recibe
credenciales ni una conexión Figma por esta validación. MCP Playwright conserva
su uso bajo demanda y su template sin registrar.

## Herramientas fijadas y reproducción

Toolchain de usuario **persistente** en `~/.local/share/choms-skills/runtime-v1`,
sin instalación global. La ruta /tmp original solo conserva evidencia de preparación. toolchain/package-lock.json fija
también transitivas con integridad npm; ejecutar `npm ci --ignore-scripts --no-audit
--no-fund` en una copia temporal de package.json y package-lock.json. Requiere Node
24 según Agent Browser. Las versiones exactas, hashes de Node/Gitleaks/FFmpeg/ffprobe,
wheel YAML y parser Hermes están en toolchain/receipt.json. No se actualizaron
paquetes del sistema. Binarios, node_modules, vídeos y capturas quedan fuera de Git.

Node portable: obtener el tar linux-x64 de la versión del recibo desde
https://nodejs.org/dist/, verificar SHA-256 antes de extraer. Los hashes de archivo
se contrastaron con los checksums oficiales publicados; no se afirma firma independiente.
Gitleaks se obtuvo del release oficial indicado en el recibo y se contrastó con sus
checksums. FFmpeg/ffprobe se contrastaron por hash de descarga; no hay firma upstream
independiente acreditada. Binarios GPL de FFmpeg no se redistribuyen en este repo.

Instalar las dos revisiones de Chromium correspondientes ejecutando, desde la copia
local fijada, `node node_modules/playwright/cli.js install chromium` y
`node node_modules/@playwright/test/cli.js install chromium`, con
`PLAYWRIGHT_BROWSERS_PATH` apuntando a su directorio temporal `browsers`.
CLI/MCP usan revisión 1247, suite @playwright/test revisión 1248. Los SHA-256 de los
executables probados figuran en NEXT_VALIDATION.json; no se confunden con el commit
upstream ni con la integridad del tarball npm.

Comandos (sustituir rutas de herramientas por el entorno local fijado):

```sh
python3 scripts/skills/local_tools.py find browser
python3 scripts/skills/local_tools.py brief tools/choms-skills/fixtures/design-brief.json
python3 scripts/skills/local_tools.py html tools/choms-skills/fixtures/browser.html
python3 scripts/skills/mcp_probe.py -- python3 scripts/skills/design_mcp.py
node scripts/skills/browser_qa.cjs --tool-root /tmp/choms-skills-env --output /tmp/nueva-evidencia
python3 scripts/skills/cli_smoke.py --tool-root /tmp/choms-skills-env --node /ruta/node
python3 scripts/skills/local_tools.py measure clip.mp4 --genre ejemplo --ffmpeg /ruta/ffmpeg --ffprobe /ruta/ffprobe
python3 scripts/skills/local_tools.py export clip.mp4 /tmp/nuevo.mp4 --width 640 --height 640 --ffmpeg /ruta/ffmpeg --ffprobe /ruta/ffprobe
```

Los runners de navegador solo prueban el fixture incluido. El runner de suite bloquea
recursos ajenos al loopback; los smoke CLI operan con HTML sin recursos externos,
sesiones temporales y cierre explícito. El host impide el sandbox Chromium: la suite
usa el valor por defecto Playwright sin sandbox y los smoke CLI/MCP lo deshabilitan
explícitamente **solo en fixtures**. No es un navegador endurecido para sitios ajenos.
MCP Playwright se probó con `--headless --isolated --no-sandbox --executable-path
/ruta/chrome --allowed-origins http://127.0.0.1:*`; esta allowlist no es una frontera
de seguridad. El template no fuerza no-sandbox para futuros usos.

Para parsers: obtener del commit Hermes del recibo agent/skill_utils.py,
hermes_constants.py y hermes_yaml.py, verificar sus hashes y disponer del wheel
ruamel.yaml fijado. Se carga skill_utils directamente, sin inicializar el paquete
agent ni sus proveedores. Ejecutar con PYTHONPATH al wheel extraído:
`python3 scripts/skills/parse_runtimes.py --hermes-source /ruta/fuente-hermes`.
El parser real y yaml_load se ejecutan; no se sustituye Hermes por un parser propio.

Pruebas offline: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/tests
-p 'test_skills_next.py'` y el mismo comando con `test_choms_skills_profile.py`.
`python3 scripts/skills/validate_profile.py`; `git diff --check`.
Gitleaks dir se ejecuta con --redact sobre copia temporal **solo** de los archivos
del bloque, sin recorrer históricos, credenciales ni directorios personales.

## Evidencia y límites

ACTIVATION_VALIDATION.json registra los resultados actuales; NEXT_VALIDATION.json
conserva la fase previa. No se incluyen datos personales.
Lint estructural no certifica accesibilidad; la captura estable y su mutación
prueban la comparación visual, no fidelidad de una app real sin referencia suministrada.
El MCP stdio es un fixture acotado, no un SDK completo ni un servicio productivo.
Las estadísticas YUV muestreadas no son un grade perceptual; un export técnico
no acredita revisión editorial, derechos de assets ni aprobación para publicar.
Figma remoto no tiene una versión/binario con hash que pueda fijarse aquí.

No se tocó scripts/memory, stacks/kubernetes/choms-memory, aceptación Memory,
Terraform, Kubernetes, Restic, NAS, OmniRoute ni servicios. Salud de servicios y
drift Kubernetes **no consultados por aislamiento explícito**, no se declara Ready
actual ni drift cero productivo. Cierre Git contra origin/main tras el merge normal autorizado. Rollback Git mediante
revert del merge revisando su primer padre; rollback de activación con el recibo
exacto indicado arriba. No hay servicios permanentes ni credenciales nuevas.
