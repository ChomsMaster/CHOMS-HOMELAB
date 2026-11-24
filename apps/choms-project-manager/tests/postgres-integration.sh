#!/usr/bin/env bash
# Runs against a disposable PostgreSQL instance with the production init script.
set -euo pipefail

cd "$(dirname "$0")/.."
python_bin=${PYTHON_BIN:-python3}
manifest=../../stacks/kubernetes/choms-project-manager/workload.yaml
image=$(awk '/image: .*pgvector/ {print $2; exit}' "$manifest")
test_tmp=$(mktemp -d)
container="career-test-$(basename "$test_tmp" | tr '[:upper:].' '[:lower:]-')"
cleanup() {
  docker rm --force --volumes "$container" >/dev/null 2>&1 || true
  rm -f "$test_tmp/01-career.sh" "$test_tmp/env" "$test_tmp/dump"
  rmdir "$test_tmp"
}
trap cleanup EXIT

awk '
  /^  01-career.sh: \|$/ { enabled = 1; next }
  enabled && /^    / { print substr($0, 5); next }
  enabled { exit }
' "$manifest" >"$test_tmp/01-career.sh"
test -s "$test_tmp/01-career.sh"
chmod 0555 "$test_tmp/01-career.sh"
export PGPASSWORD=$("$python_bin" -c 'import secrets; print(secrets.token_hex(24))')
admin_password=$("$python_bin" -c 'import secrets; print(secrets.token_hex(24))')
(
  umask 077
  printf 'POSTGRES_PASSWORD=%s\nCAREER_DB_PASSWORD=%s\n' "$admin_password" "$PGPASSWORD" >"$test_tmp/env"
)
unset admin_password

docker run --detach --name "$container" --user 999:999 --cap-drop ALL \
  --security-opt no-new-privileges --publish 127.0.0.1::5432 \
  --volume /var/lib/postgresql/data \
  --mount "type=bind,src=$test_tmp/01-career.sh,dst=/docker-entrypoint-initdb.d/01-career.sh,readonly" \
  --env-file "$test_tmp/env" --env POSTGRES_USER=postgres --env POSTGRES_DB=career \
  --env PGDATA=/var/lib/postgresql/data/pgdata "$image" >/dev/null
docker_ready() {
  for ((attempt=0; attempt<40; attempt++)); do
    if docker exec "$container" pg_isready -q -h 127.0.0.1 -d career; then return; fi
    sleep 1
  done
  printf '%s\n' 'Isolated PostgreSQL did not become ready.' >&2
  return 1
}
docker_ready
export PGHOST=127.0.0.1 PGUSER=career PGDATABASE=career
export PGPORT
refresh_port() {
  PGPORT=$(docker port "$container" 5432/tcp | awk -F: 'NR == 1 { print $NF }')
}
refresh_port
export CAREER_TEST_POSTGRES=1
export PYTHONDONTWRITEBYTECODE=1
unset CAREER_SEED_FILE PGOPTIONS

"$python_bin" -m unittest discover -s tests -v
if [[ ${RUN_BROWSER_E2E:-0} == 1 ]]; then
  PYTHONPATH=. "$python_bin" tests/browser_e2e.py
fi
"$python_bin" server.py migrate
"$python_bin" - <<'PY'
import store

with store.connect() as db:
    role = db.execute(
        "SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls "
        "FROM pg_roles WHERE rolname = current_user"
    ).fetchone()
    assert role is not None and not any(role)
    store.create_project(db, "restore-project", {"title": "Synthetic restore project"})
    store.create(db, "restore-project", "activities", "restore-fixture", {"title": "Synthetic recovery marker"})
PY

docker restart "$container" >/dev/null
docker_ready
refresh_port
"$python_bin" - <<'PY'
import store

with store.connect() as db:
    assert store.ready(db)
    assert store.find_locked(db, "restore-project", "activities", "restore-fixture")[0]["title"] == "Synthetic recovery marker"
PY
printf '%s\n' 'PostgreSQL restart passed.'

(
  umask 077
  docker exec "$container" sh -ec 'PGPASSWORD="$CAREER_DB_PASSWORD" pg_dump -h 127.0.0.1 -U career -Fc career' >"$test_tmp/dump"
)
docker exec "$container" createdb -U postgres -O career career_restore
docker exec -i "$container" sh -ec 'PGPASSWORD="$CAREER_DB_PASSWORD" pg_restore -h 127.0.0.1 -U career --no-owner --exit-on-error -d career_restore' <"$test_tmp/dump"
PGDATABASE=career_restore "$python_bin" - <<'PY'
import store

with store.connect() as db:
    assert store.ready(db)
    assert store.find_locked(db, "restore-project", "activities", "restore-fixture")[0]["title"] == "Synthetic recovery marker"
PY
printf '%s\n' 'Restore to isolated database passed.'

if [[ -n ${CAREER_TEST_PRIVATE_SEED:-} ]]; then
  docker exec "$container" createdb -U postgres -O career private_seed_test
  PGDATABASE=private_seed_test CAREER_SEED_FILE="$CAREER_TEST_PRIVATE_SEED" "$python_bin" - <<'PY'
import server

server.migrate()
server.app.config.update(CAREER_ALLOWED_USER="synthetic", CAREER_ORIGIN="https://project.test")
headers = {"Remote-User": "synthetic", "Origin": "https://project.test"}
client = server.app.test_client()
response = client.get("/api/projects/initial-project/export", headers=headers)
assert response.status_code == 200
original = response.get_json()
assert original["tasks"] and original["schedule"] and not original["activities"]
response = client.post("/api/projects/import", headers=headers, json=original)
assert response.status_code == 201
copy = response.get_json()["id"]
response = client.get(f"/api/projects/{copy}/export", headers=headers)
assert response.status_code == 200
restored = response.get_json()
assert all(original[key] == restored[key] for key in ("tasks", "schedule", "activities", "plan_overrides"))
print("Private seed initialization and isolated export/import roundtrip passed.")
PY
fi
