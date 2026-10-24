#!/usr/bin/env bash

set -euo pipefail
set +x

MODE="${1:-status}"
NAS_REMOTE="${CHOMS_NAS_REMOTE:-chomsmaster@192.168.1.167}"
KUBE_REMOTE="${CHOMS_KUBE_REMOTE:-chomsmaster@192.168.1.138}"
SSH_OPTS=(-F /dev/null)
METRIC_FILE=/home/chomsmaster/choms-node-exporter/textfile/choms_monitoring_synthetic.prom
ALERT=CHOMSMonitoringSyntheticCritical

fail() { echo "ERROR: $1" >&2; exit 1; }

state() {
  ssh "${SSH_OPTS[@]}" "$KUBE_REMOTE" "ALERT_NAME='$ALERT' python3 -" <<'PY'
import json
import os
import subprocess
import urllib.parse
import urllib.request

service = subprocess.check_output(
    ["kubectl", "get", "svc", "choms-monitoring-prometheus", "-n", "monitoring", "-o", "jsonpath={.spec.clusterIP}"],
    text=True,
)
query = 'ALERTS{alertname="' + os.environ["ALERT_NAME"] + '"}'
url = f"http://{service}:9090/api/v1/query?" + urllib.parse.urlencode({"query": query})
result = json.load(urllib.request.urlopen(url, timeout=10))["data"]["result"]
print(result[0]["metric"].get("alertstate", "inactive") if result else "inactive")
PY
}

wait_for() {
  local expected="$1"
  local attempts=40
  local current
  while (( attempts > 0 )); do
    current="$(state)"
    if [[ "$current" == "$expected" ]]; then
      echo "synthetic_alert=$expected"
      return
    fi
    sleep 5
    attempts=$((attempts - 1))
  done
  fail "synthetic alert did not become $expected"
}

case "$MODE" in
  start)
    printf '%s\n' \
      '# HELP choms_monitoring_synthetic_test Controlled notification test signal.' \
      '# TYPE choms_monitoring_synthetic_test gauge' \
      'choms_monitoring_synthetic_test 1' |
      ssh "${SSH_OPTS[@]}" "$NAS_REMOTE" "install -m 0644 /dev/stdin '$METRIC_FILE'"
    wait_for firing
    ;;
  stop)
    ssh "${SSH_OPTS[@]}" "$NAS_REMOTE" "rm -f -- '$METRIC_FILE'"
    wait_for inactive
    ;;
  status)
    echo "synthetic_alert=$(state)"
    ;;
  *) fail "usage: $0 [start|stop|status]" ;;
esac
