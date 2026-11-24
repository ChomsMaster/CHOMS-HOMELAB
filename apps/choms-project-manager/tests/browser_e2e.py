"""Browser smoke test against the real app and a disposable PostgreSQL instance.

Run from the app directory with PYTHONPATH=. and Playwright installed.
The database must be an isolated test instance.
"""
import json
import os
from pathlib import Path
from threading import Thread

from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import WSGIRequestHandler, make_server

from server import app, migrate


class QuietHandler(WSGIRequestHandler):
    def log_request(self, *args, **kwargs):
        pass


def trusted_fixture(environ, start_response):
    # Model the trusted edge only in the loopback test server.
    if environ.get("PATH_INFO") != "/api/dashboard" or environ.get("HTTP_X_TEST_ANONYMOUS") is None:
        environ["HTTP_REMOTE_USER"] = "browser-fixture"
    return app(environ, start_response)


def submit(page):
    dialogue = page.get_by_role("dialog")
    dialogue.get_by_role("button", name="Guardar", exact=True).click()
    expect(dialogue).to_be_hidden(timeout=15000)


def create_project(page, title, template=None):
    page.get_by_role("button", name="+ Nuevo proyecto", exact=True).click()
    dialogue = page.get_by_role("dialog")
    dialogue.get_by_label("Nombre", exact=True).fill(title)
    if template:
        dialogue.get_by_label("Plantilla", exact=True).select_option(label=template)
    submit(page)
    expect(page.get_by_role("heading", level=1)).to_have_text(title)


def open_section(page, section):
    page.get_by_role("link", name=section, exact=True).first.click()
    expect(page.get_by_role("heading", name=section, exact=True, level=1)).to_be_visible()


def run_flow(page, url):
    expect(page.request.get(url + "/api/dashboard", headers={"X-Test-Anonymous": "1"})).not_to_be_ok()
    page.goto(url)
    expect(page.get_by_role("heading", name="Proyectos", exact=True, level=1)).to_be_visible()
    create_project(page, "Proyecto de prueba A")
    open_section(page, "Configuración")
    page.get_by_role("button", name="Editar configuración").click()
    dialogue = page.get_by_role("dialog")
    dialogue.get_by_label("Campos personalizados", exact=True).fill("owner=Responsable")
    dialogue.get_by_label("Tipos de actividad", exact=True).fill("time=Tiempo\nbilling=Facturación")
    dialogue.get_by_label("Claves de actividades financieras (separadas por comas)").fill("billing")
    dialogue.get_by_label("Indicadores", exact=True).fill("profit_cents=Beneficio neto")
    submit(page)

    open_section(page, "Tareas")
    page.get_by_role("button", name="+ Nueva tarea", exact=True).click()
    dialogue.get_by_label("Título", exact=True).fill("Hito de prueba")
    dialogue.get_by_label("Inicio", exact=True).fill("2027-01-04")
    dialogue.get_by_label("Fin", exact=True).fill("2027-01-04")
    dialogue.get_by_label("Repetición", exact=True).select_option("daily")
    dialogue.get_by_label("Repetir hasta", exact=True).fill("2027-01-06")
    dialogue.get_by_label("Responsable", exact=True).fill("Equipo A")
    submit(page)
    expect(page.get_by_text("Hito de prueba", exact=True)).to_be_visible()
    page.get_by_role("button", name="+ Nueva tarea", exact=True).click()
    dialogue.get_by_label("Título", exact=True).fill("Tarea dependiente")
    dialogue.get_by_label("Depende de", exact=True).select_option(label="Hito de prueba")
    submit(page)
    expect(page.get_by_text("Depende de: Hito de prueba", exact=False)).to_be_visible()
    row = page.get_by_role("listitem").filter(has_text="Hito de prueba").first
    row.get_by_role("button", name="Editar", exact=True).click()
    expect(dialogue.get_by_label("Responsable", exact=True)).to_have_value("Equipo A")
    dialogue.get_by_role("button", name="Cancelar", exact=True).click()
    row.get_by_role("button", name="Completar", exact=True).click()
    expect(row).to_contain_text("Completada")
    open_section(page, "Kanban")
    expect(page.get_by_text("Hito de prueba", exact=True)).to_be_visible()
    open_section(page, "Gantt")
    expect(page.get_by_role("img", name="Hito de prueba:", exact=False)).to_be_visible()
    open_section(page, "Calendario")
    page.get_by_label("Fecha", exact=True).fill("2027-01-05")
    expect(page.get_by_text("Hito de prueba", exact=True)).to_be_visible()
    page.get_by_role("button", name="Semana", exact=True).click()
    expect(page.get_by_role("button", name="Semana", exact=True)).to_have_attribute("aria-pressed", "true")
    page.get_by_role("button", name="Mes", exact=True).click()
    expect(page.get_by_label("Calendario mensual")).to_be_visible()

    open_section(page, "Registros")
    page.get_by_role("button", name="+ Nuevo registro", exact=True).click()
    dialogue.get_by_label("Tipo", exact=True).select_option("billing")
    dialogue.get_by_label("Título", exact=True).fill("Factura de prueba")
    dialogue.get_by_label("Ingresos (€)", exact=True).fill("100.00")
    dialogue.get_by_label("Costes (€)", exact=True).fill("25.00")
    submit(page)
    expect(page.get_by_text("Factura de prueba", exact=True)).to_be_visible()
    open_section(page, "Informes")
    expect(page.get_by_text("Beneficio neto", exact=True)).to_be_visible()
    expect(page.get_by_text(r"75,00", exact=False)).to_be_visible()

    with page.expect_download() as captured:
        page.get_by_role("link", name="Descargar datos").click()
    path = captured.value.path()
    payload = json.loads(path.read_text())
    assert payload["schema_version"] == 2
    assert len(payload["tasks"]) == 2
    assert len(payload["activities"]) == 1

    open_section(page, "Configuración")
    page.get_by_role("button", name="Guardar como plantilla").click()
    dialogue.get_by_label("Nombre", exact=True).fill("Plantilla de prueba")
    submit(page)
    open_section(page, "Proyectos")
    create_project(page, "Proyecto de prueba B", "Plantilla de prueba")
    open_section(page, "Registros")
    expect(page.get_by_text("Factura de prueba", exact=True)).to_have_count(0)
    open_section(page, "Proyectos")
    page.get_by_role("button", name="Importar JSON").click()
    dialogue.locator('input[type=file]').set_input_files(path)
    submit(page)
    expect(page.get_by_role("heading", name="Proyecto de prueba A", exact=False, level=1)).to_be_visible()
    open_section(page, "Registros")
    expect(page.get_by_text("Factura de prueba", exact=True)).to_be_visible()

    output = os.environ.get("CHOMS_BROWSER_SCREENSHOTS")
    if output:
        path = Path(output)
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        page.screenshot(path=path / "desktop.png")
    page.set_viewport_size({"width": 375, "height": 812})
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    open_section(page, "Calendario")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if output:
        page.screenshot(path=path / "mobile.png")
    print("Browser E2E passed: project CRUD, recurrence, dependencies, records, KPIs, templates, import/export, and 375 px layout.")


def main():
    if os.environ.get("CAREER_TEST_POSTGRES") != "1":
        raise SystemExit("Use a disposable PostgreSQL database and set CAREER_TEST_POSTGRES=1.")
    migrate()
    with make_server("127.0.0.1", 0, trusted_fixture, request_handler=QuietHandler) as server:
        url = f"http://127.0.0.1:{server.server_port}"
        app.config.update(CAREER_ALLOWED_USER="browser-fixture", CAREER_ORIGIN=url)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                page = browser.new_page(viewport={"width": 1365, "height": 900}, accept_downloads=True)
                page.set_default_timeout(8000)
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                run_flow(page, url)
                assert not errors, errors
                browser.close()
        finally:
            server.shutdown()
            thread.join()


if __name__ == "__main__":
    main()
