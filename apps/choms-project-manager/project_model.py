"""Project configuration and reusable data validation."""
from re import fullmatch

import domain

DEFAULT_CONFIG = {
    "task_kinds": {"task": "Tarea", "milestone": "Hito"},
    "statuses": {"todo": "Pendiente", "doing": "En curso", "done": "Completada"},
    "priorities": {"low": "Baja", "medium": "Media", "high": "Alta"},
    "activity_kinds": {"time": "Tiempo", "transaction": "Movimiento"},
    "financial_activity_kinds": ["transaction"],
    "custom_fields": {},
    "indicators": {
        "calendar_minutes": "Agenda", "planned_minutes": "Tiempo previsto",
        "actual_minutes": "Tiempo real", "profit_cents": "Resultado",
        "revenue_cents": "Ingresos", "cost_cents": "Costes", "completed_tasks": "Tareas completadas",
    },
    "transport_modes": {"default": "Horario base"},
    "application_stages": {},
}
KEY = r"[a-z][a-z0-9_]{0,39}"
MAX_RECORDS = 20000


def options(value):
    if not isinstance(value, dict) or len(value) > 50:
        raise domain.Invalid("Configuración inválida.")
    for key, label in value.items():
        if not fullmatch(KEY, key):
            raise domain.Invalid("Clave de configuración inválida.")
        domain.text(label, 100, required=True)
    return value


def configuration(value, previous=None):
    if not isinstance(value, dict) or value.keys() - DEFAULT_CONFIG.keys():
        raise domain.Invalid("Configuración inválida.")
    result = {**DEFAULT_CONFIG, **(previous or {}), **value}
    for key in result.keys() - {"financial_activity_kinds"}:
        options(result[key])
    for key in ("task_kinds", "statuses", "priorities", "activity_kinds", "transport_modes"):
        if not result[key]:
            raise domain.Invalid("Debe haber al menos una opción por grupo.")
    if "done" not in result["statuses"] or "todo" not in result["statuses"]:
        raise domain.Invalid("Los estados deben incluir las claves todo y done.")
    financial = result["financial_activity_kinds"]
    if not isinstance(financial, list) or any(
        not isinstance(key, str) or key not in result["activity_kinds"] for key in financial
    ):
        raise domain.Invalid("Categorías económicas inválidas.")
    allowed_indicators = {
        *DEFAULT_CONFIG["indicators"], "monthly_revenue_cents",
        *(f"{key}_minutes" for key in result["activity_kinds"]),
        *(f"{key}_count" for key in result["task_kinds"]),
    }
    if result["indicators"].keys() - allowed_indicators:
        raise domain.Invalid("Indicador desconocido.")
    return result


def goals(value):
    if not isinstance(value, list) or len(value) > 50:
        raise domain.Invalid("Objetivos inválidos.")
    return [domain.text(item, 600, required=True) for item in value]


def project(data, previous=None):
    fields = {
        "title": domain.title, "start": domain.optional_day, "end": domain.optional_day,
        "description": domain.notes, "goals": goals, "monthly_revenue_target_cents": domain.money,
        "config": lambda value: configuration(value, (previous or {}).get("config")),
    }
    if not isinstance(data, dict):
        raise domain.Invalid("Proyecto inválido.")
    selected = domain.validated(data, fields)
    payload = {
        "title": "", "start": None, "end": None, "description": "", "goals": [],
        "monthly_revenue_target_cents": 0, "config": DEFAULT_CONFIG,
        **(previous or {}), **selected,
    }
    domain.title(payload["title"])
    if payload["start"] and payload["end"] and payload["start"] > payload["end"]:
        raise domain.Invalid("El fin del proyecto debe ser igual o posterior al inicio.")
    return payload


def transport(config, request_value=None):
    modes = config["transport_modes"]
    return domain.choice(request_value or next(iter(modes)), tuple(modes))


def record_id(value):
    if not isinstance(value, str) or not fullmatch(domain.ID_PATTERN, value):
        raise domain.Invalid("Identificador inválido.")
    return value


def schedule(events, config):
    if not isinstance(events, dict) or events.keys() - config["transport_modes"].keys():
        raise domain.Invalid("Planificación inválida.")
    if any(not isinstance(blocks, list) for blocks in events.values()) or sum(map(len, events.values())) > MAX_RECORDS:
        raise domain.Invalid("Planificación demasiado extensa.")
    for blocks in events.values():
        seen = set()
        for block in blocks:
            if not isinstance(block, dict):
                raise domain.Invalid("Bloque inválido.")
            checked = domain.validated(block, {
                "id": record_id, "date": lambda value: domain.day(value).isoformat(),
                "start": domain.optional_time,
                "end": domain.optional_end,
                "title": domain.title, "kind": lambda value: domain.text(value, 40, required=True),
                "notes": domain.notes, "provisional": domain.boolean,
            })
            if not checked.keys() >= {"id", "date", "start", "end", "title", "kind"} or checked["id"] in seen:
                raise domain.Invalid("Bloque incompleto o duplicado.")
            if not checked["start"] or not checked["end"] or checked["start"] == checked["end"]:
                raise domain.Invalid("Horario del bloque inválido.")
            seen.add(checked["id"])
    return events


def dependencies(identifier, task, all_tasks):
    graph = {item["id"]: item.get("depends_on", []) for item in all_tasks}
    graph[identifier] = task["depends_on"]
    visited = set()
    pending = list(task["depends_on"])
    while pending:
        current = pending.pop()
        if current == identifier or current not in graph:
            raise domain.Invalid("Dependencia circular o de otro proyecto.")
        if current not in visited:
            visited.add(current)
            pending.extend(graph[current])
