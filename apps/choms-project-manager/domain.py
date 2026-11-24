"""Validation and calendar/report calculations shared by the REST endpoints."""
from datetime import date, datetime, time, timedelta
from re import fullmatch
from zoneinfo import ZoneInfo

MADRID = ZoneInfo("Europe/Madrid")
ID_PATTERN = r"[A-Za-z0-9_-]{1,100}"
class Invalid(ValueError):
    pass


def today():
    return datetime.now(MADRID).date()


def text(value, limit, *, required=False):
    if not isinstance(value, str) or len(value) > limit or "\0" in value:
        raise Invalid(f"Introduce texto de hasta {limit} caracteres.")
    value = value.strip()
    if required and not value:
        raise Invalid("El título es obligatorio.")
    return value


def choice(value, options):
    if value not in options:
        raise Invalid(f"Valor inválido. Opciones: {', '.join(options)}.")
    return value


def integer(value, limit):
    if type(value) is not int or not 0 <= value <= limit:
        raise Invalid(f"Introduce un número entero entre 0 y {limit}.")
    return value


def boolean(value):
    if type(value) is not bool:
        raise Invalid("Introduce un valor booleano.")
    return value


def day(value):
    if not isinstance(value, str) or not fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise Invalid("Usa fechas con el formato AAAA-MM-DD.")
    try:
        result = date.fromisoformat(value)
    except ValueError:
        raise Invalid("La fecha no es válida.") from None
    if not 2000 <= result.year <= 2100:
        raise Invalid("La fecha debe estar entre 2000 y 2100.")
    return result


def optional_day(value):
    return None if value is None else day(value).isoformat()


def optional_time(value):
    if value is None:
        return value
    if not isinstance(value, str) or not fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
        raise Invalid("Usa horas con el formato HH:MM.")
    return value


def optional_end(value):
    return value if value == "24:00" else optional_time(value)


def duration(value):
    return integer(value, 525600)


def money(value):
    return integer(value, 1000000000)


def title(value):
    return text(value, 160, required=True)


def notes(value):
    return text(value, 4000)


def identifiers(value):
    if not isinstance(value, list) or len(value) > 50 or any(
        not isinstance(item, str) or not fullmatch(ID_PATTERN, item) for item in value
    ) or len(set(value)) != len(value):
        raise Invalid("Dependencias inválidas.")
    return value


def recurrence(value):
    if value is None:
        return None
    if not isinstance(value, dict) or value.keys() != {"frequency", "until"}:
        raise Invalid("Recurrencia inválida.")
    return {
        "frequency": choice(value["frequency"], ("daily", "weekly")),
        "until": day(value["until"]).isoformat(),
    }


TASK_FIELDS = {
    "title": title,
    "notes": notes,
    "start_date": optional_day,
    "end_date": optional_day,
    "planned_minutes": duration,
    "actual_minutes": duration,
    "provisional": boolean,
    "depends_on": identifiers,
    "recurrence": recurrence,
}
TASK_DEFAULTS = {
    "title": "", "notes": "", "kind": "task", "status": "todo", "priority": "medium",
    "start_date": None, "end_date": None, "planned_minutes": 0,
    "actual_minutes": 0, "provisional": False, "completed_on": None,
    "application_stage": None, "depends_on": [], "recurrence": None, "custom_fields": {},
}
ACTIVITY_FIELDS = {
    "title": title,
    "notes": notes,
    "date": lambda value: day(value).isoformat(),
    "planned_minutes": duration,
    "actual_minutes": duration,
    "revenue_cents": money,
    "cost_cents": money,
}
ACTIVITY_DEFAULTS = {
    "title": "", "notes": "", "kind": "time", "planned_minutes": 0,
    "actual_minutes": 0, "revenue_cents": 0, "cost_cents": 0, "custom_fields": {},
}
PLAN_FIELDS = {"title": title, "notes": notes, "start": optional_time, "end": optional_end, "hidden": boolean}


def validated(values, fields):
    if not isinstance(values, dict) or values.keys() - fields.keys():
        raise Invalid("El cuerpo debe ser un objeto con campos reconocidos.")
    return {field: fields[field](value) for field, value in values.items()}


def custom_values(values, config):
    if not isinstance(values, dict) or values.keys() - config["custom_fields"].keys():
        raise Invalid("Campos personalizados inválidos.")
    return {key: text(value, 500) for key, value in values.items()}


def task(values, previous=None, *, config):
    options = {
        "kind": lambda value: choice(value, tuple(config["task_kinds"])),
        "status": lambda value: choice(value, tuple(config["statuses"])),
        "priority": lambda value: choice(value, tuple(config["priorities"])),
        "application_stage": lambda value: None if value is None else choice(value, tuple(config["application_stages"])),
        "custom_fields": lambda value: custom_values(value, config),
    }
    result = {
        **TASK_DEFAULTS, "kind": next(iter(config["task_kinds"])),
        "priority": "medium" if "medium" in config["priorities"] else next(iter(config["priorities"])),
        **(previous or {}), **validated(values, {**TASK_FIELDS, **options}),
    }
    title(result["title"])
    start, end = result["start_date"], result["end_date"]
    if start and end and end < start:
        raise Invalid("La fecha de fin debe ser igual o posterior a la de inicio.")
    series = result["recurrence"]
    if series and (not start or (end is not None and end != start) or series["until"] < start):
        raise Invalid("Una serie recurrente requiere fecha inicial, sin intervalo de varios días.")
    result["completed_on"] = (result["completed_on"] or today().isoformat()) if result["status"] == "done" else None
    return result


def activity(values, previous=None, *, config):
    options = {
        "kind": lambda value: choice(value, tuple(config["activity_kinds"])),
        "custom_fields": lambda value: custom_values(value, config),
    }
    result = {
        **ACTIVITY_DEFAULTS, "date": today().isoformat(), "kind": next(iter(config["activity_kinds"])),
        **(previous or {}), **validated(values, {**ACTIVITY_FIELDS, **options}),
    }
    title(result["title"])
    if result["kind"] not in config["financial_activity_kinds"] and (
        result["revenue_cents"] or result["cost_cents"]
    ):
        raise Invalid("Los importes requieren una categoría económica.")
    return result


def task_events(tasks, start, end):
    for item in tasks:
        first = item["start_date"] or item["end_date"]
        last = item["end_date"] or first
        if not first or not last:
            continue
        origin = day(first)
        series = item.get("recurrence")
        step = 7 if series and series["frequency"] == "weekly" else 1
        current = max(origin, start)
        if series:
            current += timedelta(days=(-(current - origin).days) % step)
            last = series["until"]
        through = min(day(last), end)
        while current <= through:
            yield {
                "id": f"task-{item['id']}-{current}",
                "task_id": item["id"], "date": current.isoformat(), "title": item["title"],
                "start": None, "end": None, "kind": item["kind"], "status": item["status"],
                "provisional": item["provisional"], "notes": item["notes"],
            }
            current += timedelta(days=step)


def calendar(seed_plan, tasks, overrides, start, end, transport):
    events = []
    for base_event in seed_plan(start, end, transport):
        event = {**base_event, **overrides.get(base_event["id"], {})}
        if not event.get("hidden"):
            events.append(event)
    events.extend(task_events(tasks, start, end))
    return sorted(events, key=lambda event: (event["date"], event.get("start") or "", event["id"]))


def report(selected, tasks, activities, events, config):
    first = selected - timedelta(days=selected.weekday())
    last = first + timedelta(days=6)
    start, end = first.isoformat(), last.isoformat()
    week = [item for item in activities if start <= item["date"] <= end]
    completed = [item for item in tasks if start <= (item.get("completed_on") or "") <= end]
    def total(key, kind=None):
        return sum(item[key] for item in week if kind is None or item["kind"] == kind)

    scheduled = 0
    for event in events:
        if event.get("start") and event.get("end"):
            from_time = time.fromisoformat(event["start"])
            start_minute = from_time.hour * 60 + from_time.minute
            if event["end"] == "24:00":
                end_minute = 24 * 60
            else:
                to_time = time.fromisoformat(event["end"])
                end_minute = to_time.hour * 60 + to_time.minute
            scheduled += (end_minute - start_minute) % (24 * 60)

    revenue = total("revenue_cents")
    costs = total("cost_cents")
    activity_minutes = {key: total("actual_minutes", key) for key in config["activity_kinds"]}
    task_counts = {key: sum(
        item["kind"] == key and start <= (item["start_date"] or item["end_date"] or "") <= end
        for item in tasks
    ) for key in config["task_kinds"]}
    month = selected.isoformat()[:7]
    return {
        **{f"{kind}_minutes": minutes for kind, minutes in activity_minutes.items()},
        **{f"{kind}_count": count for kind, count in task_counts.items()},
        "start": start, "end": end, "calendar_minutes": scheduled,
        "planned_minutes": total("planned_minutes") + sum(
            item["planned_minutes"] for item in tasks
            if start <= (item["end_date"] or item["start_date"] or "") <= end
        ),
        "actual_minutes": total("actual_minutes") + sum(item["actual_minutes"] for item in completed),
        "activity_minutes_by_kind": activity_minutes,
        "task_count_by_kind": task_counts,
        "revenue_cents": revenue, "cost_cents": costs, "profit_cents": revenue - costs,
        "monthly_revenue_cents": sum(
            item["revenue_cents"] for item in activities
            if item["date"].startswith(month)
        ),
        "completed_tasks": len(completed),
    }
