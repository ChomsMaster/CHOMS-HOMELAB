# Puestos CHOMS: base publicada y particularidades locales

`BASE.json` declara una base Linux x86_64 para node-dev-01, node-dev-02 y futuros
puestos compatibles. Fija el lock del runtime existente, el perfil y sus trece
skills, versiones npm y siete artefactos, y una entrada MCP local de Playwright.
No instala Codex/Hermes ni cambia sus modelos, toolsets, OAuth o sesiones. Esas
aplicaciones son prerrequisitos externos y pueden conservar versiones particulares.

El coordinador `scripts/skills/workstation.py` no es otro instalador: delega toda
preparación, aceptación, integridad, activación y rollback de herramientas a
`runtime.py`, y usa `activate_native.py` para los enlaces reversibles existentes.
El runtime conserva sus versiones; la receta 3 añade inspección sin escrituras y
binding del controlador a la fuente publicada inmutable.

## Base y opcionales por equipo

La base tiene Node 24.22.2, Playwright CLI 0.1.22/MCP 0.0.83, Agent Browser 0.41.0,
Chromium 1247/1248, FFmpeg/ffprobe 7.0.2, Gitleaks 8.30.1, PyYAML 6.0.3 y el perfil
CHOMS 1.5.0. Los locks originales siguen siendo la autoridad de tarballs y hashes;
no hay otra resolución de paquetes ni lifecycle scripts npm.

hosts contiene perfiles para node-dev-01 (A2141), node-dev-02 (iMac) y default.
Son datos offline, no destinos remotos. Las operaciones solo afectan el equipo
local; no hay SSH, administración de servicios ni acceso a plataformas.

ComfyUI figura como capacidad **opcional externa**, preserve: no se inspecciona,
instala, inicia ni descarga ningún modelo. Figma es también preserve: su entrada,
OAuth y sesiones no se trasladan ni se sustituyen. Activar/provisionar nuevas
capacidades requiere una implementación revisada y otra autorización; declarar
una capacidad externa no acredita que esté instalada. Otros sistemas/arquitecturas
se rechazan antes de aplicar hasta disponer de un lock de runtime soportado.

## Fuente validada y publicada

check/plan/apply leen objetos Git de un commit, no archivos de trabajo sin publicar.
Se exige una referencia explícita origin/..., y --revision permite fijar un commit
inmutable que sea antecesor de esa referencia. La integridad del perfil, helpers,
locks, versiones y manifiesto se comprueba antes de planificar. apply reconsulta
el head remoto con ls-remote; si cambió respecto a la referencia obtenida, exige
fetch y nuevo plan. El coordinador no hace pull, reset, stash ni fetch automático.

apply comprueba además que sus tres controladores coinciden con los publicados;
un cambio local en ellos bloquea la aplicación, sin descartarlo. Cambios en otros
archivos/proyectos no son entrada de instalación y se conservan. Usar una copia
validada separada o un worktree creado manualmente si esos controladores tienen
trabajo sin publicar; nunca limpiar automáticamente el checkout del usuario.

La fuente se materializa bajo `~/.local/share/choms-workstation/sources/COMMIT`,
solo para scripts/skills, tools/choms-skills y tools/choms-workstations. No copia
hogares ni otros proyectos, código de Memory, Kubernetes, cachés, historiales,
credenciales o .git. Las skills nuevas y el launcher del runtime apuntan a esa
fuente inmutable y no dependen del checkout mutable para su ejecución.

## Check, plan, apply

Ejecutar localmente, sin sudo. Obtener referencias es una operación explícita del
operador. En esta fase se usa únicamente la rama publicada, sin merge a main:

```sh
git fetch origin
python3 scripts/skills/workstation.py check --ref origin/feat/dev-workstation-sync
python3 scripts/skills/workstation.py plan --ref origin/feat/dev-workstation-sync
python3 scripts/skills/workstation.py apply --ref origin/feat/dev-workstation-sync --expect-plan PLAN_SHA256
```

Sustituir PLAN_SHA256 por el valor emitido por el plan revisado. --source permite
indicar el checkout Git del que se leen los objetos; --revision COMMIT fija una
base determinada. No introducir tokens ni valores OAuth en ningún argumento.
check devuelve 0 si converge y 1 si hay diferencias; plan devuelve 0 si es viable,
aunque muestre acciones. Los conflictos o datos no válidos producen salida de
fallo. check y plan no crean directorios, fuentes, locks, recibos, configuraciones
ni instalaciones y no inician herramientas/MCP. Sus hashes de precondiciones no
contienen valores de configuración. La referencia local puede estar desactualizada:
solo apply exige la comprobación de publicación remota.

apply vuelve a comprobar precondiciones antes y después de preparar herramientas,
valida el perfil con el validador existente y exige aceptación del runtime antes
de promocionar. Si ya converge no hace escrituras. Una nueva publicación que solo
cambia documentación no fuerza reinstalar si el contrato y contenidos siguen iguales.
Las pruebas funcionales del runtime solo usan fixtures locales, loopback y vídeo
sintético; no generan inferencias ni servicios permanentes.

## Propiedad y preservación

- Solo gestiona los trece nombres CHOMS del perfil y choms_playwright en config
  nativa Codex/Hermes. No habilita hooks, publicación social o administración de skills.
- Conserva el texto y campos ajenos de configuración; nunca guarda copias completas
  de esa configuración en los recibos. Solo registra la entrada MCP propia, enlaces
  y estado del runtime. OAuth/credenciales no se abren, exportan o sincronizan.
- Archivos propios ajenos o enlaces modificados no se sobrescriben. Un MCP existente
  distinto bloquea apply. Una entrada equivalente preexistente puede conservarse sin
  reclamar propiedad. Los symlinks de configuración se remiten a revisión manual.
- Enlaces CHOMS con recibo legado verificable se migran a snapshots inmutables tras
  comparar todo el paquete, sin modificar su checkout ni el contenido de la skill.
  Los enlaces equivalentes sin prueba de propiedad se conservan; futuras colisiones
  requieren revisión. Los trece contenidos siguen iguales a la fuente publicada.
- Los recibos privados están bajo ~/.local/share/choms-workstation/transactions.
  Se valida que no haya cambios posteriores antes del rollback. No se borran fuentes,
  releases o cachés como parte de una reversión.

## Rollback

```sh
python3 scripts/skills/workstation.py rollback --ref origin/feat/dev-workstation-sync
```

Revierte la última transacción activa: solo enlaces creados/retargeteados, entrada
MCP propia y pointers/launcher anteriores del runtime. Preserva entradas y cambios
ajenos posteriores. Si una entrada propia fue modificada, falla antes de editar
nada y exige revisión; no hay opción force. Los fallos parciales de apply intentan
esta compensación con su journal, sin restaurar hogares ni configuraciones enteras.
Un rollback no desinstala paquetes del sistema (no se instalaron), borra assets o
toca sesiones. Conservar la fuente aprobada para ejecutar su mismo coordinador.

## Incorporar otro puesto o actualizar bajo demanda

1. Obtener localmente el repositorio y sus refs, sin tocar un checkout con trabajo
   pendiente. Mantener Python >=3.12 y las bibliotecas del host requeridas por Chromium.
2. Seleccionar el commit publicado aprobado; revisar BASE.json y las particularidades
   del perfil de equipo o default. ComfyUI y Figma permanecen fuera del aprovisionamiento.
3. Ejecutar check y plan, resolver colisiones sin sobrescrituras y aplicar ese plan.
4. Repetir check; inspeccionar los recibos. No se programa una sincronización automática.
5. Para actualizar: publicar primero el manifiesto/locks revisados en una rama, obtener
   refs manualmente, elegir el commit nuevo y repetir el mismo flujo. No hay latest ni
   actualización automática de proveedores. No se requiere que todos los hogares sean iguales.

El A2141 no se contacta ni aplica desde node-dev-02. Su aplicación local queda para
después de su trabajo actual. [VALIDATION.json](VALIDATION.json) distingue pruebas
con hogares/orígenes aislados de las observaciones reales del iMac.

## Resultado real del iMac — 2026-10-30

Contra la fuente publicada 1173d0b, check/plan identifican 29 acciones y ningún
conflicto: receta/controlador 1 (sin upgrade de herramientas), 26 enlaces CHOMS
con propiedad acreditada para binding a la fuente inmutable y dos entradas MCP
choms_playwright (Codex y Hermes). Los fingerprints de configuraciones y enlaces
no cambian durante check/plan. El informe privado se guardó con la autorización
del entorno; no se cambiaron permisos del sistema.

No se aplicó la base a la instalación real. Figma y configuraciones ajenas se
conservaron; ComfyUI y el A2141 no se inspeccionaron ni provisionaron. apply y su
segunda ejecución sin cambios, bootstrap funcional y rollback se acreditaron en
un hogar aislado con el instalador existente (20 checks browser, 25 tools MCP y
exportación sintética con audio). Los 57 tests ya aprobados no se repitieron para
resolver el guardado. Para usar el plan guardado, fijar --revision 1173d0b; si se
elige otro commit o cambian inputs locales, generar y revisar un plan nuevo.
