#!/usr/bin/env bash

set -euo pipefail
set +x

MODE="${1:-plan}"
ROOT="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$ROOT/compose.yaml"
REMOTE="${SCRUTINY_NAS_REMOTE:-chomsmaster@192.168.1.167}"
REMOTE_DIR="${SCRUTINY_NAS_REMOTE_DIR:-/home/chomsmaster/choms-scrutiny-collector}"
SSH_OPTS=(-F /dev/null)
CONTAINER=choms-scrutiny-collector
ROLLBACK_CONTAINER=choms-scrutiny-collector-rollback
ENDPOINT=https://scrutiny.chomsmaster.com
IMAGE='ghcr.io/analogj/scrutiny@sha256:3274a8c1e4b48bcc42089f9431f89604d4b3a661aeeaa2029c59c352d41762c2'

fail() {
  echo "ERROR: $1" >&2
  exit 1
}

case "$MODE" in
  plan|apply) ;;
  *) fail "usage: $0 [plan|apply]" ;;
esac

for command_name in ssh scp python3; do
  command -v "$command_name" >/dev/null 2>&1 || fail "$command_name is required"
done
test -s "$COMPOSE_FILE" || fail "missing compose.yaml"

remote() {
  ssh "${SSH_OPTS[@]}" "$REMOTE" "$@"
}

validate_current_contract() {
  remote "docker inspect '$CONTAINER'" | python3 -c '
import json
import sys

expected = {
    "image": sys.argv[1],
    "host_id": "choms-nas",
    "schedule": "0 */6 * * *",
    "startup": "true",
    "privileged": True,
    "network": "bridge",
    "restart": "unless-stopped",
    "binds": {"/dev:/dev", "/run/udev:/run/udev:ro"},
}
x = json.load(sys.stdin)[0]
c, h = x["Config"], x["HostConfig"]
env = dict(v.split("=", 1) for v in c.get("Env", []) if "=" in v)
actual = {
    "image": c["Image"],
    "host_id": env.get("COLLECTOR_HOST_ID"),
    "schedule": env.get("COLLECTOR_CRON_SCHEDULE"),
    "startup": env.get("COLLECTOR_RUN_STARTUP"),
    "privileged": h.get("Privileged"),
    "network": h.get("NetworkMode"),
    "restart": h.get("RestartPolicy", {}).get("Name"),
    "binds": set(h.get("Binds") or []),
}
if actual != expected:
    raise SystemExit("effective collector contract differs from the declared baseline")
endpoint = env.get("COLLECTOR_API_ENDPOINT")
if endpoint not in {"http://192.168.1.138:8083", sys.argv[2]}:
    raise SystemExit("unexpected collector endpoint")
print("effective_contract=validated")
print("endpoint_change=" + endpoint + " -> " + sys.argv[2])
' "$IMAGE" "$ENDPOINT"
}

validate_render() {
  remote "temp=\$(mktemp -d /tmp/choms-scrutiny-compose.XXXXXX); trap 'rm -rf -- \"\$temp\"' EXIT; install -m 0600 /dev/stdin \"\$temp/compose.yaml\"; docker compose -f \"\$temp/compose.yaml\" config --quiet; docker compose -f \"\$temp/compose.yaml\" config --format json" < "$COMPOSE_FILE" |
    python3 -c '
import json
import sys

render = json.load(sys.stdin)["services"]
if set(render) != {"collector"}:
    raise SystemExit("render contains an unexpected service")
s = render["collector"]
expected = {
    "image": sys.argv[1], "container_name": "choms-scrutiny-collector",
    "command": ["/entrypoint-collector.sh"], "privileged": True,
    "network_mode": "bridge", "restart": "unless-stopped",
    "security_opt": ["label=disable"],
    "environment": {
        "COLLECTOR_API_ENDPOINT": sys.argv[2],
        "COLLECTOR_HOST_ID": "choms-nas",
        "COLLECTOR_RUN_STARTUP": "true",
        "COLLECTOR_CRON_SCHEDULE": "0 */6 * * *",
    },
}
for key, value in expected.items():
    if s.get(key) != value:
        raise SystemExit("unexpected rendered field: " + key)
volumes = {(v["source"], v["target"], v.get("read_only", False)) for v in s.get("volumes", [])}
if volumes != {("/dev", "/dev", False), ("/run/udev", "/run/udev", True)}:
    raise SystemExit("unexpected rendered mounts")
text = json.dumps(render).lower()
for forbidden in ("docker.sock", "password", "token", "secret"):
    if forbidden in text:
        raise SystemExit("forbidden field in rendered collector config: " + forbidden)
print("compose_render=validated")
' "$IMAGE" "$ENDPOINT"
}

validate_endpoint() {
  remote "code=\$(curl --connect-timeout 5 --max-time 10 -sS -o /dev/null -w '%{http_code}' '$ENDPOINT/api/health'); test \"\$code\" = 200; echo endpoint_health=validated"
}

snapshot_identities() {
  local destination="$1"
  remote "SCRUTINY_SUMMARY_URL='$ENDPOINT/api/summary' python3 -" > "$destination" <<'PY'
import hashlib
import json
import os
import urllib.request

summary = json.load(urllib.request.urlopen(os.environ["SCRUTINY_SUMMARY_URL"], timeout=10))["data"]["summary"]
all_ids = []
nas_ids = []
for summary_id, record in summary.items():
    device = record.get("device", {})
    identity = str(summary_id)
    digest = hashlib.sha256(identity.encode()).hexdigest()
    all_ids.append(digest)
    if device.get("host_id") == "choms-nas":
        nas_ids.append(digest)
if len(nas_ids) != 5 or len(set(nas_ids)) != 5:
    raise SystemExit("NAS identity baseline is not exactly five unique devices")
print("all=" + ",".join(sorted(all_ids)))
print("nas=" + ",".join(sorted(nas_ids)))
PY
}

validate_current_contract
validate_render
validate_endpoint

if [[ "$MODE" == plan ]]; then
  echo "remote_diff=collector endpoint only; declaration will be installed at $REMOTE_DIR/compose.yaml"
  exit 0
fi

umask 077
temp_dir="$(mktemp -d)"
before="$temp_dir/before"
after="$temp_dir/after"
cleanup() {
  rm -f -- "$before" "$after"
  rmdir -- "$temp_dir"
}
trap cleanup EXIT HUP INT TERM

snapshot_identities "$before"
remote "test ! -e '$ROLLBACK_CONTAINER'; install -d -m 0700 '$REMOTE_DIR'"
scp "${SSH_OPTS[@]}" "$COMPOSE_FILE" "$REMOTE:$REMOTE_DIR/compose.yaml" >/dev/null

rollback() {
  trap - ERR
  set +e
  remote "docker rm -f '$CONTAINER' >/dev/null 2>&1 || true; docker rename '$ROLLBACK_CONTAINER' '$CONTAINER'; docker start '$CONTAINER' >/dev/null"
  echo "ERROR: collector validation failed; previous container restored" >&2
  exit 1
}
trap rollback ERR

remote "docker stop '$CONTAINER' >/dev/null; docker rename '$CONTAINER' '$ROLLBACK_CONTAINER'; cd '$REMOTE_DIR'; docker compose up -d --no-deps collector"

remote "deadline=120; while [ \"\$deadline\" -gt 0 ]; do logs=\$(docker logs --since 3m '$CONTAINER' 2>&1); if printf '%s' \"\$logs\" | grep -q 'Main: Completed'; then break; fi; sleep 3; deadline=\$((deadline-3)); done; test \"\$deadline\" -gt 0; ! printf '%s' \"\$logs\" | grep -Eq 'Post .* (timeout|refused)|level=error.*(API|Post|publish|register)'; count=\$(printf '%s' \"\$logs\" | grep -c 'smartctl --info --json /dev/'); test \"\$count\" -eq 5; echo collection=completed devices=5 publication_errors=0"

snapshot_identities "$after"
cmp -s "$before" "$after" || fail "device identities changed or duplicate records appeared"

remote "SCRUTINY_SUMMARY_URL='$ENDPOINT/api/summary' python3 -" <<'PY'
import datetime
import json
import os
import urllib.request

now = datetime.datetime.now(datetime.timezone.utc)
summary = json.load(urllib.request.urlopen(os.environ["SCRUTINY_SUMMARY_URL"], timeout=10))["data"]["summary"]
nas = [r for r in summary.values() if r.get("device", {}).get("host_id") == "choms-nas"]
if len(nas) != 5:
    raise SystemExit("expected five NAS records")
for record in nas:
    raw = record.get("smart", {}).get("collector_date", "")
    stamp = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if (now - stamp).total_seconds() > 300:
        raise SystemExit("NAS record was not refreshed by the immediate collection")
print("central_ingestion=five_recent_same_identities")
PY

remote "cd '$REMOTE_DIR'; docker compose config --quiet; docker inspect -f 'collector_status={{.State.Status}} restarts={{.RestartCount}}' '$CONTAINER'; docker rm '$ROLLBACK_CONTAINER' >/dev/null; echo rollback_container=removed"
trap - ERR
echo "NAS Scrutiny collector restored successfully."
