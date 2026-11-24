"""Project-scoped PostgreSQL store and transactional schema migrations."""
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

MIGRATIONS = Path(__file__).parent / "migrations"
INITIAL_PROJECT = "initial-project"


def connect():
    return psycopg.connect(connect_timeout=5, application_name="choms-project-manager")


def migrations():
    return sorted(MIGRATIONS.glob("[0-9][0-9][0-9]_*.sql"))


def migrate(initial=None):
    with connect() as db:
        db.execute("SELECT pg_advisory_xact_lock(735226921)")
        db.execute("""
            CREATE TABLE IF NOT EXISTS career_migrations (
                version text PRIMARY KEY,
                applied_at timestamptz NOT NULL DEFAULT now()
            )
        """)
        applied = {row[0] for row in db.execute("SELECT version FROM career_migrations")}
        for migration in migrations():
            if migration.stem not in applied:
                db.execute(migration.read_text(encoding="utf-8"))
                db.execute("INSERT INTO career_migrations(version) VALUES (%s)", (migration.stem,))
        if "project_seed_v2" in applied:
            return
        if initial:
            metadata, tasks, schedule = initial
            legacy = read_project(db, INITIAL_PROJECT)
            if legacy:
                update_project(db, INITIAL_PROJECT, metadata, schedule)
            else:
                create_project(db, INITIAL_PROJECT, metadata, schedule)
            for item in tasks:
                payload = {key: value for key, value in item.items() if key != "id"}
                db.execute(
                    "INSERT INTO career_records (project_id,kind,id,payload) VALUES (%s,'tasks',%s,%s) "
                    "ON CONFLICT DO NOTHING", (INITIAL_PROJECT, item["id"], Jsonb(payload)),
                )
            db.execute("INSERT INTO career_migrations(version) VALUES ('project_seed_v2')")


def ready(db):
    applied = {row[0] for row in db.execute("SELECT version FROM career_migrations")}
    db.execute("SELECT 1 FROM pm_projects LIMIT 1")
    return {path.stem for path in migrations()} <= applied


def read_project(db, identifier, *, lock=False):
    query = "SELECT payload, schedule FROM pm_projects WHERE id = %s"
    if lock:
        query += " FOR UPDATE"
    return db.execute(query, (identifier,)).fetchone()


def projects(db):
    return [{"id": identifier, **payload} for identifier, payload in db.execute(
        "SELECT id,payload FROM pm_projects ORDER BY payload->>'title',id"
    )]


def create_project(db, identifier, payload, schedule=None):
    db.execute("INSERT INTO pm_projects (id,payload,schedule) VALUES (%s,%s,%s)",
               (identifier, Jsonb(payload), Jsonb(schedule or {})))


def update_project(db, identifier, payload, schedule):
    db.execute("UPDATE pm_projects SET payload=%s,schedule=%s WHERE id=%s",
               (Jsonb(payload), Jsonb(schedule), identifier))


def templates(db):
    return [{"id": identifier, **payload} for identifier, payload in db.execute(
        "SELECT id,payload FROM pm_templates ORDER BY payload->>'title',id"
    )]


def template(db, identifier):
    row = db.execute("SELECT payload FROM pm_templates WHERE id=%s", (identifier,)).fetchone()
    return row[0] if row else None


def create_template(db, identifier, payload):
    db.execute("INSERT INTO pm_templates (id,payload) VALUES (%s,%s)", (identifier, Jsonb(payload)))


def rows(db, project_id, category):
    return [
        {"id": record_id, **payload}
        for record_id, payload in db.execute(
            "SELECT id,payload FROM career_records WHERE project_id=%s AND kind=%s ORDER BY id",
            (project_id, category),
        )
    ]


def find_locked(db, project_id, category, record_id):
    return db.execute(
        "SELECT payload FROM career_records WHERE project_id=%s AND kind=%s AND id=%s FOR UPDATE",
        (project_id, category, record_id),
    ).fetchone()


def create(db, project_id, category, record_id, payload):
    db.execute(
        "INSERT INTO career_records (project_id,kind,id,payload) VALUES (%s,%s,%s,%s)",
        (project_id, category, record_id, Jsonb(payload)),
    )


def update(db, project_id, category, record_id, payload):
    db.execute(
        "UPDATE career_records SET payload=%s WHERE project_id=%s AND kind=%s AND id=%s",
        (Jsonb(payload), project_id, category, record_id),
    )


def update_override(db, project_id, record_id, payload):
    db.execute("""
        INSERT INTO career_records (project_id,kind,id,payload) VALUES (%s,'plan',%s,%s)
        ON CONFLICT (project_id,kind,id) DO UPDATE SET payload=career_records.payload || excluded.payload
    """, (project_id, record_id, Jsonb(payload)))
