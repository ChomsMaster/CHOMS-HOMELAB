"""Project Manager REST application. Identity is asserted by the isolated gateway."""
from datetime import timedelta
from functools import wraps
from graphlib import CycleError, TopologicalSorter
from hmac import compare_digest
import os
from pathlib import Path
import sys
from uuid import uuid4

from flask import Flask, abort, jsonify, request, send_from_directory
from psycopg import Error as DatabaseError
from werkzeug.exceptions import HTTPException

import domain
import project_model
import seed
import store

STATIC = Path(__file__).parent / "static"
MCP_ENDPOINTS = {"projects", "project", "tasks", "plan", "weekly", "complete_task", "create_activity"}
app = Flask(__name__, static_folder=None)
app.config.from_mapping(
    CAREER_ALLOWED_USER=os.environ.get("CAREER_ALLOWED_USER", ""),
    CAREER_ORIGIN=os.environ.get("CAREER_ORIGIN", ""),
    CAREER_API_TOKEN=os.environ.get("CAREER_API_TOKEN", ""),
    MAX_CONTENT_LENGTH=16 * 1024,
)


def fail(message, code):
    return jsonify(error=message), code


def identical(provided, expected):
    return bool(expected) and compare_digest(provided.encode(), expected.encode())


@app.before_request
def authenticate():
    if request.endpoint == "import_project":
        request.max_content_length = 6 * 1024 * 1024
    if request.endpoint in ("health", "ready"):
        return None
    bearer = app.config["CAREER_API_TOKEN"]
    if len(bearer) >= 32 and request.endpoint in MCP_ENDPOINTS and identical(
        request.headers.get("Authorization", ""), f"Bearer {bearer}"
    ):
        return None
    user = request.headers.get("Remote-User", "")
    if not user:
        return fail("Se requiere autenticación.", 401)
    if "," in user or not identical(user, app.config["CAREER_ALLOWED_USER"]):
        return fail("Sin autorización para este espacio privado.", 403)
    if request.method in ("POST", "PATCH", "PUT", "DELETE") and not identical(
        request.headers.get("Origin", ""), app.config["CAREER_ORIGIN"]
    ):
        return fail("Origen de la solicitud inválido.", 403)
    return None


@app.after_request
def secure_response(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self'; base-uri 'none'; "
        "frame-ancestors 'none'; form-action 'self'"
    )
    return response


@app.errorhandler(domain.Invalid)
def invalid(error):
    return fail(str(error), 400)


@app.errorhandler(DatabaseError)
def database_error(_error):
    return fail("La base de datos no está disponible.", 503)


@app.errorhandler(HTTPException)
def http_error(error):
    return fail(error.name, error.code)


def database(function):
    @wraps(function)
    def route(*args, **kwargs):
        with store.connect() as db:
            return function(db, *args, **kwargs)
    return route


@app.get("/healthz")
def health():
    return jsonify(status="ok")


@app.get("/readyz")
@database
def ready(db):
    return (jsonify(status="ready"), 200) if store.ready(db) else fail("Inicialización pendiente.", 503)


@app.get("/")
def index():
    return send_from_directory(STATIC, "index.html")


@app.get("/<any(app.js,style.css,icon.svg):filename>")
def asset(filename):
    return send_from_directory(STATIC, filename)


def normalize_project(payload):
    return project_model.project(payload)


def scoped(db, identifier, *, lock=False):
    project_model.record_id(identifier)
    row = store.read_project(db, identifier, lock=lock)
    if row is None:
        abort(404)
    return normalize_project(row[0]), row[1]


@app.get("/api/projects")
@database
def projects(db):
    return jsonify([
        {"id": item["id"], **normalize_project({k: v for k, v in item.items() if k != "id"})}
        for item in store.projects(db)
    ])


@app.get("/api/dashboard")
@database
def dashboard(db):
    db.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
    result = {"projects": [], "tasks": 0, "completed_tasks": 0, "activities": 0,
              "revenue_cents": 0, "cost_cents": 0, "profit_cents": 0}
    for item in store.projects(db):
        identifier = item["id"]
        tasks = store.rows(db, identifier, "tasks")
        activities = store.rows(db, identifier, "activities")
        summary = {"tasks": len(tasks), "completed_tasks": sum(task["status"] == "done" for task in tasks),
                   "activities": len(activities), "revenue_cents": sum(row["revenue_cents"] for row in activities),
                   "cost_cents": sum(row["cost_cents"] for row in activities)}
        summary["profit_cents"] = summary["revenue_cents"] - summary["cost_cents"]
        result["projects"].append({**item, **summary})
        for key, value in summary.items():
            result[key] += value
    return jsonify(result)


def body():
    value = request.get_json()
    if not isinstance(value, dict):
        raise domain.Invalid("El cuerpo debe ser un objeto.")
    return value


@app.post("/api/projects")
@database
def create_project(db):
    payload = body()
    template_id = payload.pop("template_id", None)
    template = None
    if template_id is not None:
        template = store.template(db, project_model.record_id(template_id))
        if template is None:
            return fail("Plantilla no encontrada.", 404)
        payload.setdefault("config", template["config"])
    identifier = str(uuid4())
    project = normalize_project(payload)
    store.create_project(db, identifier, project)
    return jsonify(id=identifier, **project), 201


@app.get("/api/projects/<project_id>")
@database
def project(db, project_id):
    metadata, _ = scoped(db, project_id)
    return jsonify(id=project_id, **metadata)


@app.patch("/api/projects/<project_id>")
@database
def patch_project(db, project_id):
    previous, schedule = scoped(db, project_id, lock=True)
    metadata = project_model.project(body(), previous)
    config = metadata["config"]
    project_model.schedule(schedule, config)
    # Reject removing options that still describe existing records.
    for collection, normalizer in (("tasks", domain.task), ("activities", domain.activity)):
        for item in store.rows(db, project_id, collection):
            normalizer({k: v for k, v in item.items() if k not in ("id", "completed_on")}, config=config)
    store.update_project(db, project_id, metadata, schedule)
    return jsonify(id=project_id, **metadata)


@app.get("/api/templates")
@database
def templates(db):
    return jsonify(store.templates(db))


@app.post("/api/templates")
@database
def create_template(db):
    payload = domain.validated(body(), {"project_id": project_model.record_id, "title": domain.title})
    if payload.keys() != {"project_id", "title"}:
        raise domain.Invalid("Indica el proyecto y un título.")
    metadata, _ = scoped(db, payload["project_id"])
    template = {"title": payload["title"], "config": metadata["config"]}
    identifier = str(uuid4())
    store.create_template(db, identifier, template)
    return jsonify(id=identifier, **template), 201


@app.get("/api/projects/<project_id>/tasks")
@database
def tasks(db, project_id):
    scoped(db, project_id)
    return jsonify(store.rows(db, project_id, "tasks"))


@app.get("/api/projects/<project_id>/activities")
@database
def activities(db, project_id):
    scoped(db, project_id)
    return jsonify(store.rows(db, project_id, "activities"))


def task_constraints(db, project_id, record_id, payload):
    tasks = store.rows(db, project_id, "tasks")
    project_model.dependencies(record_id, payload, tasks)
    prerequisites = set(payload["depends_on"])
    if payload["status"] == "done" and any(
        row["id"] in prerequisites and row["status"] != "done" for row in tasks
    ):
        raise domain.Invalid("Completa las tareas de las que depende antes de cerrar esta tarea.")
    if payload["status"] != "done" and any(
        row["status"] == "done" and record_id in row.get("depends_on", ()) for row in tasks
    ):
        raise domain.Invalid("Reabre primero las tareas completadas que dependen de ésta.")


def create_record(db, project_id, category, normalizer):
    metadata, _ = scoped(db, project_id, lock=True)
    record_id = str(uuid4())
    payload = normalizer(body(), config=metadata["config"])
    if category == "tasks":
        task_constraints(db, project_id, record_id, payload)
    store.create(db, project_id, category, record_id, payload)
    return jsonify(id=record_id, **payload), 201


def update_record(db, project_id, category, record_id, normalizer, payload=None):
    metadata, _ = scoped(db, project_id, lock=True)
    project_model.record_id(record_id)
    record = store.find_locked(db, project_id, category, record_id)
    if record is None:
        return fail("Registro no encontrado.", 404)
    payload = normalizer(body() if payload is None else payload, record[0], config=metadata["config"])
    if category == "tasks":
        task_constraints(db, project_id, record_id, payload)
    store.update(db, project_id, category, record_id, payload)
    return jsonify(id=record_id, **payload)


@app.post("/api/projects/<project_id>/tasks")
@database
def create_task(db, project_id):
    return create_record(db, project_id, "tasks", domain.task)


@app.patch("/api/projects/<project_id>/tasks/<record_id>")
@database
def patch_task(db, project_id, record_id):
    return update_record(db, project_id, "tasks", record_id, domain.task)


@app.post("/api/projects/<project_id>/tasks/<record_id>/complete")
@database
def complete_task(db, project_id, record_id):
    return update_record(db, project_id, "tasks", record_id, domain.task, {"status": "done"})


@app.post("/api/projects/<project_id>/activities")
@database
def create_activity(db, project_id):
    return create_record(db, project_id, "activities", domain.activity)


@app.patch("/api/projects/<project_id>/activities/<record_id>")
@database
def patch_activity(db, project_id, record_id):
    return update_record(db, project_id, "activities", record_id, domain.activity)


def plan_range(schedule, first, last, transport):
    return [event for event in schedule.get(transport, ()) if first.isoformat() <= event["date"] <= last.isoformat()]


def calendar(db, project_id, schedule, start, end, transport, tasks=None):
    overrides = {
        item["id"]: {key: value for key, value in item.items() if key != "id"}
        for item in store.rows(db, project_id, "plan")
    }
    return domain.calendar(
        lambda first, last, mode: plan_range(schedule, first, last, mode),
        store.rows(db, project_id, "tasks") if tasks is None else tasks,
        overrides, start, end, transport,
    )


@app.get("/api/projects/<project_id>/plan")
@database
def plan(db, project_id):
    metadata, schedule = scoped(db, project_id)
    start = domain.day(request.args.get("start", domain.today().isoformat()))
    end = domain.day(request.args.get("end", start.isoformat()))
    if not 0 <= (end - start).days <= 62:
        raise domain.Invalid("El rango de calendario debe ser de hasta 63 días.")
    transport = project_model.transport(metadata["config"], request.args.get("transport"))
    return jsonify(calendar(db, project_id, schedule, start, end, transport))


def plan_changes(values):
    delta = domain.validated(values, domain.PLAN_FIELDS)
    if ("start" in delta) != ("end" in delta):
        raise domain.Invalid("Indica las horas de inicio y fin juntas.")
    if "start" in delta and (bool(delta["start"]) != bool(delta["end"]) or delta["start"] == delta["end"] and delta["start"]):
        raise domain.Invalid("Indica dos horas distintas o vacía ambas.")
    return delta


@app.patch("/api/projects/<project_id>/plan/<record_id>")
@database
def patch_plan(db, project_id, record_id):
    metadata, schedule = scoped(db, project_id, lock=True)
    project_model.record_id(record_id)
    transport = project_model.transport(metadata["config"], request.args.get("transport"))
    base = next((event for event in schedule.get(transport, ()) if event["id"] == record_id), None)
    if base is None:
        return fail("Bloque de planificación no encontrado.", 404)
    store.update_override(db, project_id, record_id, plan_changes(body()))
    current = store.find_locked(db, project_id, "plan", record_id)[0]
    return jsonify({**base, **current})


@app.get("/api/projects/<project_id>/reports/weekly")
@database
def weekly(db, project_id):
    db.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
    metadata, schedule = scoped(db, project_id)
    config = metadata["config"]
    selected = domain.day(request.args.get("date", domain.today().isoformat()))
    transport = project_model.transport(config, request.args.get("transport"))
    monday = selected - timedelta(days=selected.weekday())
    tasks = store.rows(db, project_id, "tasks")
    return jsonify(domain.report(
        selected, tasks, store.rows(db, project_id, "activities"),
        calendar(db, project_id, schedule, monday, monday + timedelta(days=6), transport, tasks), config,
    ))


@app.get("/api/projects/<project_id>/export")
@database
def export(db, project_id):
    db.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
    metadata, schedule = scoped(db, project_id)
    response = jsonify(
        schema_version=2, project={"id": project_id, **metadata}, schedule=schedule,
        tasks=store.rows(db, project_id, "tasks"), activities=store.rows(db, project_id, "activities"),
        plan_overrides=store.rows(db, project_id, "plan"),
    )
    response.headers["Content-Disposition"] = 'attachment; filename="choms-project-export.json"'
    return response


def imported_records(collection, normalize):
    if not isinstance(collection, list) or len(collection) > project_model.MAX_RECORDS:
        raise domain.Invalid("Colección inválida.")
    records = {}
    for item in collection:
        if not isinstance(item, dict):
            raise domain.Invalid("Registro inválido.")
        identifier = project_model.record_id(item.get("id"))
        if identifier in records:
            raise domain.Invalid("Identificador duplicado.")
        records[identifier] = normalize({key: value for key, value in item.items() if key != "id"})
    return records


@app.post("/api/projects/import")
@database
def import_project(db):
    data = body()
    if data.keys() != {"schema_version", "project", "schedule", "tasks", "activities", "plan_overrides"} or data["schema_version"] != 2:
        raise domain.Invalid("Formato de exportación inválido.")
    if not isinstance(data["project"], dict):
        raise domain.Invalid("Proyecto inválido.")
    metadata = normalize_project({key: value for key, value in data["project"].items() if key != "id"})
    config = metadata["config"]
    schedule = project_model.schedule(data["schedule"], config)
    def normalize_task(item):
        completed = domain.optional_day(item.pop("completed_on", None))
        value = domain.task(item, config=config)
        if value["status"] == "done" and completed:
            value["completed_on"] = completed
        return value

    tasks = imported_records(data["tasks"], normalize_task)
    activities = imported_records(data["activities"], lambda item: domain.activity(item, config=config))
    overrides = imported_records(data["plan_overrides"], plan_changes)
    base_ids = {item["id"] for blocks in schedule.values() for item in blocks}
    if overrides.keys() - base_ids:
        raise domain.Invalid("Una excepción carece de bloque base.")
    graph = {identifier: value["depends_on"] for identifier, value in tasks.items()}
    for identifier, prerequisites in graph.items():
        if set(prerequisites) - tasks.keys():
            raise domain.Invalid("Dependencia de otro proyecto.")
        if tasks[identifier]["status"] == "done" and any(tasks[dep]["status"] != "done" for dep in prerequisites):
            raise domain.Invalid("Una tarea completada tiene dependencias pendientes.")
    try:
        tuple(TopologicalSorter(graph).static_order())
    except CycleError:
        raise domain.Invalid("Dependencia circular.") from None
    project_id = str(uuid4())
    store.create_project(db, project_id, metadata, schedule)
    for category, records in (("tasks", tasks), ("activities", activities), ("plan", overrides)):
        for identifier, item in records.items():
            store.create(db, project_id, category, identifier, item)
    return jsonify(id=project_id, **metadata), 201


def migrate():
    filename = os.environ.get("CAREER_SEED_FILE")
    if not filename:
        store.migrate()
        return
    raw, tasks, schedule = seed.load_seed(filename)
    allowed = {"title", "start", "end", "description", "goals", "config", "monthly_revenue_target_cents"}
    metadata = normalize_project({key: value for key, value in raw.items() if key in allowed})
    config = metadata["config"]
    project_model.schedule(schedule, config)
    initial_tasks = [
        {"id": project_model.record_id(item["id"]), **domain.task(
            {key: value for key, value in item.items() if key != "id"}, config=config,
        )}
        for item in tasks
    ]
    store.migrate((metadata, initial_tasks, schedule))


if __name__ == "__main__":
    if sys.argv[1:] != ["migrate"]:
        sys.exit("Uso: python server.py migrate")
    try:
        migrate()
    except (DatabaseError, domain.Invalid, RuntimeError):
        sys.exit("No se pudo aplicar la migración de Project Manager.")
