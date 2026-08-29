#!/usr/bin/env bash

set -euo pipefail

MODE="${1:-plan}"
ROOT="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REMOTE="${CHOMS_NAS_REMOTE:-chomsmaster@192.168.1.167}"
REMOTE_DIR="${CHOMS_NAS_NODE_EXPORTER_DIR:-/home/chomsmaster/choms-node-exporter}"
SSH_OPTS=(-F /dev/null)

fail() { echo "ERROR: $1" >&2; exit 1; }
case "$MODE" in plan|apply) ;; *) fail "usage: $0 [plan|apply]" ;; esac
for command_name in ssh scp python3; do
  command -v "$command_name" >/dev/null 2>&1 || fail "$command_name is required"
done

python3 - "$ROOT/choms-nas-metrics.py" <<'PY'
import pathlib
import sys
compile(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"), sys.argv[1], "exec")
PY
remote() { ssh "${SSH_OPTS[@]}" "$REMOTE" "$@"; }

remote "test \"\$(loginctl show-user chomsmaster -p Linger --value)\" = yes; if test -e '$REMOTE_DIR'; then test -f '$REMOTE_DIR/compose.yaml'; test -f /home/chomsmaster/.config/systemd/user/choms-nas-metrics.service; test -f /home/chomsmaster/.config/systemd/user/choms-nas-metrics.timer; test \"\$(docker inspect -f '{{.Name}}' choms-nas-node-exporter)\" = /choms-nas-node-exporter; else test ! -e /home/chomsmaster/.config/systemd/user/choms-nas-metrics.service; test ! -e /home/chomsmaster/.config/systemd/user/choms-nas-metrics.timer; ! ss -ltn 'sport = :9100' | grep -q LISTEN; fi; docker compose version >/dev/null; systemctl --user is-system-running >/dev/null"

remote "temp=\$(mktemp -d /tmp/choms-node-exporter.XXXXXX); trap 'rm -rf -- \"\$temp\"' EXIT; install -m 0600 /dev/stdin \"\$temp/compose.yaml\"; docker compose -f \"\$temp/compose.yaml\" config --quiet; docker compose -f \"\$temp/compose.yaml\" config --format json" < "$ROOT/compose.yaml" |
  python3 -c '
import json, sys
r=json.load(sys.stdin)["services"]
if set(r)!={"node-exporter"}: raise SystemExit("unexpected service in render")
s=r["node-exporter"]
if s.get("privileged",False): raise SystemExit("exporter must not be privileged")
if s.get("cap_drop") != ["ALL"]: raise SystemExit("capabilities are not fully dropped")
if s.get("read_only") is not True: raise SystemExit("root filesystem is not read-only")
if s.get("user") != "65534:65534": raise SystemExit("unexpected exporter user")
text=json.dumps(r).lower()
for forbidden in ("docker.sock","/dev:/dev","password","token","secret"):
    if forbidden in text: raise SystemExit("forbidden rendered field: "+forbidden)
print("compose_render=validated")'

verify_dir="$(mktemp -d)"
trap 'rm -rf -- "$verify_dir"' EXIT HUP INT TERM
sed 's#^ExecStart=.*#ExecStart=/bin/true#' \
  "$ROOT/systemd/choms-nas-metrics.service" > "$verify_dir/choms-nas-metrics.service"
cp "$ROOT/systemd/choms-nas-metrics.timer" "$verify_dir/"
systemd-analyze verify \
  "$verify_dir/choms-nas-metrics.service" \
  "$verify_dir/choms-nas-metrics.timer" >/dev/null
rm -rf -- "$verify_dir"
trap - EXIT HUP INT TERM

if [[ "$MODE" == plan ]]; then
  echo "remote_diff=managed node-exporter container, textfile script, service and timer only"
  exit 0
fi

remote "install -d -m 0700 '$REMOTE_DIR'"
scp "${SSH_OPTS[@]}" "$ROOT/compose.yaml" "$ROOT/choms-nas-metrics.py" "$REMOTE:$REMOTE_DIR/" >/dev/null
scp "${SSH_OPTS[@]}" "$ROOT/systemd/choms-nas-metrics.service" "$ROOT/systemd/choms-nas-metrics.timer" "$REMOTE:$REMOTE_DIR/" >/dev/null

rollback() {
  trap - ERR
  set +e
  remote "cd '$REMOTE_DIR'; docker compose down >/dev/null 2>&1 || true; systemctl --user disable --now choms-nas-metrics.timer >/dev/null 2>&1 || true; rm -f /home/chomsmaster/.config/systemd/user/choms-nas-metrics.service /home/chomsmaster/.config/systemd/user/choms-nas-metrics.timer '$REMOTE_DIR/textfile/choms_nas.prom'; systemctl --user daemon-reload"
  echo "ERROR: NAS exporter deployment failed and was rolled back" >&2
  exit 1
}
trap rollback ERR

remote "install -d -m 0755 '$REMOTE_DIR/textfile' /home/chomsmaster/.config/systemd/user; install -m 0644 '$REMOTE_DIR/choms-nas-metrics.service' /home/chomsmaster/.config/systemd/user/choms-nas-metrics.service; install -m 0644 '$REMOTE_DIR/choms-nas-metrics.timer' /home/chomsmaster/.config/systemd/user/choms-nas-metrics.timer; systemctl --user daemon-reload; systemctl --user start choms-nas-metrics.service; systemctl --user enable choms-nas-metrics.timer; systemctl --user restart choms-nas-metrics.timer; cd '$REMOTE_DIR'; docker compose up -d --no-deps node-exporter"

remote "test \"\$(systemctl --user show choms-nas-metrics.service -p Result --value)\" = success; systemctl --user is-active --quiet choms-nas-metrics.timer; test \"\$(docker inspect -f '{{.State.Status}}' choms-nas-node-exporter)\" = running; test \"\$(curl -sS -o /dev/null -w '%{http_code}' http://192.168.1.167:9100/metrics)\" = 200; echo nas_exporter=validated"
trap - ERR
