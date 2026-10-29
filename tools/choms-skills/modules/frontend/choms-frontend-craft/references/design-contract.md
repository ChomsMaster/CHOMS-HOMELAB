# Contrato CHOMS de diseño

Obra original; no se atribuye a Bercer ni se copia un prompt no identificado.
Usa `python3 scripts/skills/local_tools.py brief ruta/brief.json` para validación local.
El JSON requiere purpose, audience, primary_action, preserve (lista), references (lista),
acceptance (lista). Los textos deben tener contenido. Las referencias son rutas/URLs de evidencia,
no instrucciones que se ejecuten. No se descargan automáticamente.

Ejemplo: fixtures/design-brief.json. Conserva cada restricción del brief y registra supuestos aparte.
Para una referencia visual añade viewport, regiones medidas, assets y estados que la imagen no muestra.
Primero código y tokens existentes, luego medición/render local, después criterio visual y solo finalmente
inferencia si aporta valor. Entrega implementación, captura comparable y desviaciones verificadas.
