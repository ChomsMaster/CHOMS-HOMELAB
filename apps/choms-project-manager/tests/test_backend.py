"""Unit and opt-in PostgreSQL integration tests for the project engine."""
import os
from datetime import date
from pathlib import Path
import json
import tempfile
from unittest.mock import patch
import unittest
from uuid import uuid4

import psycopg
from psycopg import sql

import domain
import project_model
import server
import store

HEADERS = {"Remote-User": "test-user", "Origin": "https://career.test"}
TOKEN = "example-test-token-only-not-for-deployment"
CONFIG = project_model.DEFAULT_CONFIG
SAMPLE_DAY = date(2028, 4, 3)


class DomainTest(unittest.TestCase):
    def test_task_transition_and_invalid_date(self):
        pending = domain.task({"title": "Synthetic task"}, config=CONFIG)
        done = domain.task({"status": "done"}, pending, config=CONFIG)
        self.assertEqual(done["completed_on"], domain.today().isoformat())
        self.assertEqual(domain.task({"notes": "Edit"}, done, config=CONFIG)["completed_on"], done["completed_on"])
        self.assertIsNone(domain.task({"status": "todo"}, done, config=CONFIG)["completed_on"])
        with self.assertRaises(domain.Invalid):
            domain.task({"title": "Synthetic", "start_date": "2028-04-05", "end_date": "2028-04-04"}, config=CONFIG)

    def test_integral_euro_cents_and_activity_validation(self):
        for value in (True, "100", -1, 1.5):
            with self.subTest(value=value), self.assertRaises(domain.Invalid):
                domain.activity({"title": "Synthetic", "kind": "transaction", "cost_cents": value}, config=CONFIG)
        with self.assertRaises(domain.Invalid):
            domain.activity({"title": "Synthetic", "kind": "time", "revenue_cents": 200}, config=CONFIG)
        with self.assertRaises(domain.Invalid):
            domain.activity({"title": "Synthetic", "finished": "invented"}, config=CONFIG)

    def test_weekly_report_finances_and_midnight(self):
        activities = [domain.activity({
            "title": "Synthetic transaction", "kind": "transaction", "date": when,
            "revenue_cents": revenue, "cost_cents": cost, "actual_minutes": 30,
        }, config=CONFIG) for when, revenue, cost in (("2028-04-03", 8000, 2500), ("2028-04-21", 1000, 500))]
        report = domain.report(SAMPLE_DAY, [], activities, [{"start": "22:00", "end": "24:00"}], CONFIG)
        self.assertEqual(
            [report[key] for key in ("calendar_minutes", "actual_minutes", "profit_cents", "monthly_revenue_cents")],
            [120, 30, 5500, 9000],
        )

    def test_recurrence_remains_aligned_to_initial_weekday(self):
        task = {"id": "example-task", **domain.task({
            "title": "Synthetic", "start_date": "2028-04-03",
            "recurrence": {"frequency": "weekly", "until": "2028-04-23"},
        }, config=CONFIG)}
        records = list(domain.task_events([task], date(2028, 4, 4), date(2028, 4, 28)))
        self.assertEqual([item["date"] for item in records], ["2028-04-10", "2028-04-17"])

    def test_custom_options_and_indicator_validation(self):
        config = project_model.configuration({
            "activity_kinds": {"inspection": "Inspección"}, "financial_activity_kinds": [],
            "custom_fields": {"author": "Autor"}, "indicators": {"inspection_minutes": "Minutos"},
        })
        item = domain.activity({"title": "Synthetic", "kind": "inspection", "custom_fields": {"author": "Example"}}, config=config)
        self.assertEqual(item["custom_fields"], {"author": "Example"})
        with self.assertRaises(domain.Invalid):
            domain.activity({"title": "Synthetic", "custom_fields": {"unknown": "Example"}}, config=config)


class HttpTest(unittest.TestCase):
    def setUp(self):
        server.app.config.update(
            TESTING=True, CAREER_ALLOWED_USER="test-user", CAREER_ORIGIN="https://career.test", CAREER_API_TOKEN=TOKEN,
        )
        self.client = server.app.test_client()

    def test_authorization_all_private_entry_points(self):
        for path in ("/", "/app.js", "/style.css", "/api/projects", "/api/projects/test/export", "/missing"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 401)
                self.assertEqual(self.client.get(path, headers={"Remote-User": "other"}).status_code, 403)
        self.assertEqual(self.client.get("/healthz").status_code, 200)
        duplicate = [("Remote-User", "test-user"), ("Remote-User", "other")]
        self.assertEqual(self.client.get("/api/projects", headers=duplicate).status_code, 403)

    def test_csrf_and_optional_bearer(self):
        remote = {"Remote-User": "test-user", "Origin": "https://foreign.test"}
        self.assertEqual(self.client.post("/api/projects", headers=remote, json={}).status_code, 403)
        self.assertEqual(self.client.get("/missing", headers=HEADERS).status_code, 404)
        bearer = {"Authorization": f"Bearer {TOKEN}"}
        self.assertEqual(self.client.get("/api/not-a-route", headers=bearer).status_code, 401)
        self.assertEqual(self.client.get("/", headers=bearer).status_code, 401)


@unittest.skipUnless(os.environ.get("CAREER_TEST_POSTGRES") == "1", "requires isolated PostgreSQL")
class PostgresIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = f"project_test_{uuid4().hex}"
        with psycopg.connect() as db:
            db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(cls.schema)))
        cls.addClassCleanup(cls.drop_schema)
        cls.old_options = os.environ.get("PGOPTIONS")
        os.environ["PGOPTIONS"] = f"-c search_path={cls.schema}"
        server.migrate()

    @classmethod
    def drop_schema(cls):
        if cls.old_options is None:
            os.environ.pop("PGOPTIONS", None)
        else:
            os.environ["PGOPTIONS"] = cls.old_options
        with psycopg.connect() as db:
            db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(cls.schema)))

    def setUp(self):
        server.app.config.update(TESTING=True, CAREER_ALLOWED_USER="test-user", CAREER_ORIGIN="https://career.test")
        self.client = server.app.test_client()

    def call(self, method, path, data=None, status=200):
        response = self.client.open(f"/api{path}", method=method, headers=HEADERS, json=data)
        self.assertEqual(response.status_code, status, response.get_json())
        return response.get_json()

    def new_project(self, title, **fields):
        return self.call("POST", "/projects", {"title": title, **fields}, 201)["id"]

    def test_cross_project_isolation_dependencies_and_roundtrip(self):
        first = self.new_project("First fixture", config={"custom_fields": {"owner": "Owner"}})
        other = self.new_project("Second fixture")
        a, b = f"/projects/{first}", f"/projects/{other}"
        task = self.call("POST", f"{a}/tasks", {"title": "Synthetic prerequisite"}, 201)
        self.call("PATCH", f"{b}/tasks/{task['id']}", {"status": "done"}, 404)
        self.call("POST", f"{b}/tasks", {"title": "Synthetic", "depends_on": [task["id"]]}, 400)
        wrong = self.call("GET", f"{b}/export")
        self.assertEqual(wrong["tasks"], [])

        when = domain.today().isoformat()
        child = self.call("POST", f"{a}/tasks", {
            "title": "Synthetic recurring dependent", "depends_on": [task["id"]],
            "start_date": when, "planned_minutes": 45, "custom_fields": {"owner": "Fixture"},
            "recurrence": {"frequency": "daily", "until": when},
        }, 201)
        self.call("PATCH", f"{a}/tasks/{task['id']}", {"depends_on": [child["id"]]}, 400)
        self.call("PATCH", f"{a}/tasks/{child['id']}", {"status": "done"}, 400)
        bearer = {"Authorization": f"Bearer {TOKEN}"}
        self.assertEqual(self.client.get("/api" + a + "/export", headers=bearer).status_code, 401)
        self.assertEqual(self.client.patch("/api" + a + f"/tasks/{task['id']}", headers=bearer,
                                           json={"status": "done"}).status_code, 401)
        self.assertEqual(self.client.post("/api" + a + f"/tasks/{task['id']}/complete", headers=bearer).status_code, 200)
        self.call("PATCH", f"{a}/tasks/{child['id']}", {
            "status": "done", "title": "Synthetic edited", "actual_minutes": 35,
        })
        self.call("POST", f"{a}/activities", {
            "title": "Synthetic transaction", "kind": "transaction", "date": when,
            "revenue_cents": 7000, "cost_cents": 2000,
        }, 201)
        self.assertEqual(self.call("GET", f"{b}/activities"), [])
        self.assertTrue(any(event.get("task_id") == child["id"] for event in self.call("GET", f"{a}/plan")))
        self.assertEqual(self.call("GET", f"{b}/plan"), [])

        server.migrate()
        report = self.call("GET", f"{a}/reports/weekly")
        self.assertEqual((report["planned_minutes"], report["actual_minutes"], report["profit_cents"]), (45, 35, 5000))
        self.assertEqual(self.call("GET", f"{b}/reports/weekly")["profit_cents"], 0)
        original = self.call("GET", f"{a}/export")
        copied_id = self.call("POST", "/projects/import", original, 201)["id"]
        self.assertNotEqual(copied_id, first)
        copied = self.call("GET", f"/projects/{copied_id}/export")
        for key in ("tasks", "activities", "plan_overrides", "schedule"):
            self.assertEqual(copied[key], original[key])

    def test_template_and_project_configuration(self):
        source = self.new_project("Template origin", config={"custom_fields": {"team": "Equipo"}})
        template = self.call("POST", "/templates", {"title": "Synthetic template", "project_id": source}, 201)
        target = self.new_project("Template target", template_id=template["id"])
        current = self.call("GET", f"/projects/{target}")
        self.assertEqual(current["config"]["custom_fields"], {"team": "Equipo"})
        saved = self.call("PATCH", f"/projects/{target}", {"config": {"statuses": {"todo": "Por hacer", "done": "Hecha"}}})
        self.assertEqual(saved["config"]["statuses"]["done"], "Hecha")
        self.assertEqual(saved["config"]["custom_fields"], {"team": "Equipo"})
        self.assertIn(target, {item["id"] for item in self.call("GET", "/dashboard")["projects"]})

    def test_large_seed_export_import_roundtrip(self):
        blocks = [{
            "id": f"synthetic-{index}", "title": "Synthetic planning block", "date": "2028-04-03",
            "start": "22:00", "end": "24:00", "kind": "planned", "notes": "x" * 180,
            "provisional": False,
        } for index in range(4500)]
        fixture = {
            "project": {"title": "Synthetic seed", "start": "2028-04-03", "end": "2028-04-04"},
            "tasks": [{"id": "seed-task", "title": "Synthetic task"}], "plan": {"default": blocks},
        }
        with tempfile.TemporaryDirectory() as directory:
            seed_file = Path(directory) / "seed.json"
            seed_file.write_text(json.dumps(fixture), encoding="utf-8")
            with patch.dict(os.environ, {"CAREER_SEED_FILE": str(seed_file)}):
                server.migrate()
        path = "/projects/initial-project"
        self.call("PATCH", f"{path}/plan/synthetic-0", {"title": "Edited synthetic block"})
        original = self.call("GET", f"{path}/export")
        self.assertGreater(len(json.dumps(original)), 1024 * 1024)
        copy = self.call("POST", "/projects/import", original, 201)
        restored = self.call("GET", f"/projects/{copy['id']}/export")
        self.assertEqual(len(restored["schedule"]["default"]), 4500)
        self.assertEqual(restored["plan_overrides"], original["plan_overrides"])

    def test_legacy_record_migration_preserves_existing_row(self):
        with store.connect() as db:
            db.execute("DROP TABLE pm_templates, career_records, pm_projects, career_migrations")
            old = store.migrations()[0]
            db.execute(old.read_text(encoding="utf-8"))
            db.execute("CREATE TABLE career_migrations (version text PRIMARY KEY)")
            db.execute("INSERT INTO career_migrations VALUES (%s)", (old.stem,))
            db.execute(
                "INSERT INTO career_records VALUES ('tasks','legacy-record','{\"title\":\"Legacy fixture\",\"status\":\"todo\"}'::jsonb)"
            )
        server.migrate()
        original = self.call("GET", "/projects/initial-project/tasks")
        self.assertIn("legacy-record", {item["id"] for item in original})


if __name__ == "__main__":
    unittest.main()
