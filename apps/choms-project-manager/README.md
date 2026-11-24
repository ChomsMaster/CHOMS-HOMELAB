# CHOMS Project Manager

Monolito web privado con Flask/Gunicorn, interfaz en español sin compilación
frontend y PostgreSQL. Los datos y configuración de cada proyecto se guardan
dentro de su ámbito. Authelia autentica al usuario en el Gateway y la
aplicación autoriza una cuenta configurada. Esta edición sirve a un único
operador con varios proyectos.

## Pruebas y arranque

Crear un entorno Python 3.12 e instalar `requirements.txt`. Ejecutar
`python -m unittest discover -s tests -v`. Con Docker disponible, ejecutar
`PYTHON_BIN=/ruta/al/entorno/bin/python tests/postgres-integration.sh` para
ejercitar la API con PostgreSQL, reinicio y recuperación aislados.
La prueba de navegador usa Playwright con Chromium. Con una base PostgreSQL
desechable, ejecutar `PYTHONPATH=. python tests/browser_e2e.py`.

Para arrancar, exportar los parámetros `PGHOST`, `PGPORT`, `PGDATABASE`,
`PGUSER` y `PGPASSWORD` desde el almacén del entorno. Configurar
`CAREER_ALLOWED_USER` y `CAREER_ORIGIN`, ejecutar `python server.py migrate`
y arrancar Gunicorn detrás del Gateway. El archivo inicial privado se
provisiona con `CAREER_SEED_FILE`. No incluirlo en la imagen o en Git.

## API

- `/api/projects` lista o crea proyectos.
- `/api/dashboard` agrega la cartera.
- `/api/projects/{id}` consulta o actualiza la configuración.
- `/api/projects/{id}/tasks` y `/activities` registran y editan trabajo.
- `/api/projects/{id}/plan` y `/reports/weekly` exponen calendario e indicadores.
- `/api/projects/{id}/export`, `/api/projects/import` y `/api/templates`
  permiten trasladar proyectos y reutilizar su configuración.

La documentación de operación, rollback y copias está en
[el manifiesto de despliegue](../../stacks/kubernetes/choms-project-manager/README.md).
