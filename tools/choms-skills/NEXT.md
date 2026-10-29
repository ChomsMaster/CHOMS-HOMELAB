# CHOMS Skills/MCP next — bloque local 1.4.0

Rama exclusiva `feat/skills-mcp-next`, base `69a2f4b`; no merge ni despliegue.
Principio: LOCAL-FIRST, DETERMINISTIC-FIRST, AI-LAST. Cuatro módulos originales
MIT en modules/, fuera del descubrimiento global. Las nueve skills canónicas y
verification-loop permanecen byte a byte intactas. ECC sigue fijado a v2.2.3;
no se instala su bundle, memoria, hooks ni proveedores.

## Estado exacto

| Capacidad | Resultado de este bloque |
|---|---|
| frontend | Módulo preparado: complemento de dirección/sistema existentes; detalle Emil/Impeccable/Taste, contrato CHOMS, flujo Image to Code y lint HTML local |
| browser-QA | Módulo preparado; runner real Chromium, CLI Playwright y Agent Browser probados con fixture local |
| MCP-tooling | Módulo preparado; búsqueda offline, servidor stdio de validación de briefs y probe ejecutados |
| vídeo-social | Módulo preparado; medición YUV por género, metadatos y exportación fit-and-pad locales probados; publicación OFF |
| MCP Playwright | Handshake, 25 tools, navegación about:blank y cierre PASS; template sin registrar |
| MCP Figma | Templates inertes; initialize anónimo devuelve **401**; OAuth real pendiente, sin iniciar ni solicitar tokens |
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

El perfil 1.3.0 documentaba nueve enlaces en **node-dev-01**. Este checkout se ejecuta
en otro entorno: aquí se observaron **cero** enlaces CHOMS esperados en las raíces
nativas Codex/Hermes. No se modifica ese estado ni se afirma promoción global.
Los trece SKILL.md pasan descubrimiento Codex en un proyecto temporal y parseo
Hermes nativo. No se probó catálogo/slash Hermes completo: no está instalado aquí.
DISCOVERY_VALIDATION.json conserva evidencia histórica; NEXT_VALIDATION.json describe
solo esta ejecución. No se inicia ningún turno de modelo ni gateway.

PROFILE.json declara por módulo las skills existentes que reutiliza (reuse_existing).
Para usar un módulo, cargar explícitamente su SKILL.md desde este checkout.
Los comandos se ejecutan desde la raíz del repositorio. Para una promoción futura,
resolver raíces del runtime y comprobar colisiones antes de enlaces individuales;
no enlazar tools/choms-skills completo ni importar configs sin revisar.
Los templates Figma no registran conexiones; el JSON Playwright es un ejemplo
para adaptar al cliente, fuera de cualquier configuración activa. OAuth real es
el siguiente gate Figma; después harían falta tools/list y lectura del nodo autorizado.

## Herramientas fijadas y reproducción

Toolchain **temporal**, no instalada globalmente. toolchain/package-lock.json fija
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

NEXT_VALIDATION.json registra resultados agregados sin datos personales.
Lint estructural no certifica accesibilidad; la captura estable y su mutación
prueban la comparación visual, no fidelidad de una app real sin referencia suministrada.
El MCP stdio es un fixture acotado, no un SDK completo ni un servicio productivo.
Las estadísticas YUV muestreadas no son un grade perceptual; un export técnico
no acredita revisión editorial, derechos de assets ni aprobación para publicar.
Figma remoto no tiene una versión/binario con hash que pueda fijarse aquí.

No se tocó scripts/memory, stacks/kubernetes/choms-memory, aceptación Memory,
Terraform, Kubernetes, Restic, NAS, OmniRoute ni servicios. Salud de servicios y
drift Kubernetes **no consultados por aislamiento explícito**, no se declara Ready
actual ni drift cero productivo. Cierre Git contra la rama publicada; origin/main
es solo la base, sin merge. Rollback: abandonar esta rama o revertir el único
commit; no hay enlaces globales, servidores persistentes ni credenciales que retirar.
