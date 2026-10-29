---
name: choms-video-social
description: "Prepare local video and social deliverables with media metadata checks, subtitles and manual export; no automatic publishing."
license: MIT
---

Empieza por assets y metadatos locales. Reutiliza el criterio editorial de ECC content-engine y
video-editing solo donde falte: audiencia, mensaje, gancho, prueba, ritmo, subtítulos y CTA coherentes.
No adoptes memoria ECC, generación masiva, scraping, publicación ni hooks. No abras cuentas sociales.
`python3 scripts/skills/local_tools.py media /ruta/clip.mp4 --ffprobe /ruta/ffprobe` valida contenedor,
vídeo, duración y dimensiones con una salida agregada; no imprime tags ni nombres de archivos.
El gate técnico no mide taste, legibilidad, derechos o calidad de audio: revisa imagen y escucha el export.
Prepara variantes horizontal/cuadrada/vertical solo según el brief; no fuerces recorte si corta contenido.
Registra safe areas del destino vigente como restricciones del proyecto, no constantes universales.
Sin ffprobe falla explícitamente; no sustituyas evidencia por inferencia. Usa FFmpeg local fijado para
normalización/exportación solo tras elegir encuadre, fps, subtítulos y loudness con el material autorizado.
La entrega es un archivo local y un checklist de revisión humana. Publicación automática permanece OFF.

Exportación local sin recorte ni sobrescritura:
`python3 scripts/skills/local_tools.py export origen.mp4 ./salida-nueva.mp4 --width 1080 --height 1920 --ffmpeg /ruta/ffmpeg --ffprobe /ruta/ffprobe`.
Dimensiones explícitas pares, fit-and-pad, metadatos retirados y comprobación posterior del archivo.
Un fallo puede dejar salida parcial: revisarla, no publicarla ni reintentar sobrescribiendo.

Taste audiovisual local: `python3 scripts/skills/local_tools.py measure clip.mp4 --genre mi-genero --ffmpeg /ruta/ffmpeg --ffprobe /ruta/ffprobe`.
El recibo conserva hash del asset, género separado y medias Y/U/V muestreadas a 1 fps.
Reutiliza de ECC taste-distillation/taste-application el enfoque medido; esta implementación CHOMS
no incorpora sus proveedores, scripts, LUT, montaje por cadencia ni resultados de experimentos ajenos.
Las estadísticas de señal no equivalen a igualar un look perceptual; cero medido y campo ausente son distintos.

## Runtime CHOMS local

En node-dev-02 usa `~/.local/share/choms-skills/runtime/bin/choms-runtime run local-tools export origen.mp4 ./salida-nueva.mp4 --width 640 --height 640`.
El launcher resuelve la release activa, verifica su integridad y usa herramientas fijadas;
no depende de /tmp ni requiere paquetes globales. `choms-runtime` aquí significa ese
launcher por ruta completa: no se modifica PATH del usuario. Para bootstrap, actualización
controlada y rollback consulta runtime/README.md en la raíz del perfil. Los temporales
y capturas sintéticos quedan en la ubicación administrada; nunca datos personales.
