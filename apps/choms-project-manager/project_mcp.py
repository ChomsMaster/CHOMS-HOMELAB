"""MCP stdio adapter for the Project Manager REST API over an operator-only loopback tunnel."""
import json
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

import domain

DATE = {"type": "string", "format": "date"}
TITLE = {"type": "string", "minLength": 1, "maxLength": 160}
NOTES = {"type": "string", "maxLength": 4000}
MINUTES = {"type": "integer", "minimum": 0, "maximum": 525600}
CENTS = {"type": "integer", "minimum": 0, "maximum": 1000000000}
KEY = {"type": "string", "pattern": f"^{domain.ID_PATTERN}$"}
ACTIVITY = {
    "kind": KEY, "title": TITLE, "date": DATE, "actual_minutes": MINUTES,
    "planned_minutes": MINUTES, "notes": NOTES, "revenue_cents": CENTS,
    "cost_cents": CENTS, "custom_fields": {"type": "object", "additionalProperties": {"type": "string"}},
}
TOOLS = {
    "list_projects": ("Listar los proyectos accesibles.", {}, []),
    "get_daily_plan": ("Leer la agenda de un proyecto.",
                       {"date": DATE, "transport": KEY}, ["date"]),
    "get_project_status": ("Leer el proyecto y el estado de sus tareas.", {}, []),
    "get_weekly_report": ("Leer los indicadores de la semana.", {"date": DATE}, ["date"]),
    "complete_task": ("Completar una tarea del proyecto.", {"id": KEY}, ["id"]),
    "log_activity": ("Registrar una actividad con una categoría configurada en el proyecto.",
                     ACTIVITY, ["kind", "title", "date", "actual_minutes"]),
}


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def client():
    port = os.environ.get("CAREER_MCP_PORT", "18080")
    token = os.environ.get("CAREER_API_TOKEN", "")
    if not port.isascii() or not port.isdecimal() or len(port) > 5 or not 1 <= int(port) <= 65535:
        raise ValueError("Puerto MCP inválido.")
    if len(token) < 32 or any(not 33 <= ord(char) <= 126 for char in token):
        raise ValueError("Credencial MCP ausente o inválida.")
    opener = build_opener(ProxyHandler({}), NoRedirects())
    def call(path, method="GET", data=None):
        body = json.dumps(data).encode() if data is not None else None
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = Request(f"http://127.0.0.1:{port}/api/{path}", data=body, method=method, headers=headers)
        with opener.open(request, timeout=10) as response:
            return json.load(response)
    return call


def scoped_schema(name):
    _, props, required = TOOLS[name]
    if name == "list_projects":
        return props, required
    return {"project_id": KEY, **props}, ["project_id", *required]


def list_tools():
    tools = []
    for name, (description, _, _) in TOOLS.items():
        props, required = scoped_schema(name)
        readonly = name.startswith(("get_", "list_"))
        tools.append({
            "name": name, "description": description,
            "inputSchema": {"type": "object", "properties": props, "required": required,
                            "additionalProperties": False},
            "annotations": {"readOnlyHint": readonly,
                            "idempotentHint": readonly or name == "complete_task"},
        })
    return tools


def checked_key(value):
    if not isinstance(value, str) or not re.fullmatch(domain.ID_PATTERN, value):
        raise domain.Invalid("Identificador inválido.")
    return value


def invoke(call, name, args):
    if not isinstance(name, str) or name not in TOOLS:
        raise domain.Invalid("Herramienta desconocida.")
    props, required = scoped_schema(name)
    if not isinstance(args, dict) or args.keys() - props.keys() or set(required) - args.keys():
        raise domain.Invalid("Parámetros incompletos o desconocidos.")
    if name == "list_projects":
        return call("projects")
    base = "projects/" + checked_key(args["project_id"])
    if name == "get_daily_plan":
        date = domain.day(args["date"]).isoformat()
        query = {"start": date, "end": date}
        if "transport" in args:
            query["transport"] = checked_key(args["transport"])
        return call(base + "/plan?" + urlencode(query))
    if name == "get_project_status":
        return {"project": call(base), "tasks": call(base + "/tasks")}
    if name == "get_weekly_report":
        return call(base + "/reports/weekly?" + urlencode({"date": domain.day(args["date"]).isoformat()}))
    if name == "complete_task":
        record = checked_key(args["id"])
        return call(f"{base}/tasks/{record}/complete", "POST", {})
    payload = {key: value for key, value in args.items() if key != "project_id"}
    domain.day(payload["date"])
    domain.title(payload["title"])
    checked_key(payload["kind"])
    for key in ("planned_minutes", "actual_minutes"):
        if key in payload:
            domain.duration(payload[key])
    for key in ("revenue_cents", "cost_cents"):
        if key in payload:
            domain.money(payload[key])
    return call(base + "/activities", "POST", payload)


def dispatch(call, message):
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Solicitud inválida."}}
    if "id" not in message:
        return None
    reply = {"jsonrpc": "2.0", "id": message["id"]}
    method, params = message.get("method"), message.get("params", {})
    if method == "initialize":
        result = {"protocolVersion": "2025-06-18", "serverInfo": {"name": "choms-project-manager",
                  "version": "0.1.0"}, "capabilities": {"tools": {}}}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": list_tools()}
    elif method == "tools/call" and isinstance(params, dict):
        try:
            value = invoke(call, params.get("name"), params.get("arguments", {}))
            result = {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}]}
        except domain.Invalid as exc:
            result = {"isError": True, "content": [{"type": "text", "text": str(exc)}]}
        except HTTPError as exc:
            result = {"isError": True, "content": [{"type": "text", "text": f"Error HTTP {exc.code} de Career."}]}
        except (URLError, TimeoutError, ValueError):
            result = {"isError": True, "content": [{"type": "text", "text": "API de proyectos no disponible."}]}
    else:
        return {**reply, "error": {"code": -32601, "message": "Método desconocido."}}
    return {**reply, "result": result}


def main():
    try:
        call = client()
    except ValueError as exc:
        sys.exit(str(exc))
    for line in sys.stdin:
        try:
            reply = dispatch(call, json.loads(line))
        except (json.JSONDecodeError, RecursionError):
            reply = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "JSON inválido."}}
        if reply is not None:
            print(json.dumps(reply, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
