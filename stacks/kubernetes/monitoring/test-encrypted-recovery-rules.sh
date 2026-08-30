#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VALUES="$ROOT/values.yaml"
PROMETHEUS_IMAGE='quay.io/prometheus/prometheus@sha256:64f71bb84e03c855948418b0fc5dea53e9543d8e3fc9931598f583805507f05e'
umask 077
temp_dir="$(mktemp -d)"
cleanup() { rm -rf -- "$temp_dir"; }
trap cleanup EXIT HUP INT TERM

python3 - "$VALUES" "$temp_dir/choms-encrypted-recovery.rules.yaml" <<'PY'
import sys
import yaml

with open(sys.argv[1], encoding="utf-8") as source:
    values = yaml.safe_load(source)
groups = values["additionalPrometheusRulesMap"]["choms-actionable-storage"]["groups"]
selected = [group for group in groups if group["name"] == "choms-encrypted-recovery"]
if len(selected) != 1:
    raise RuntimeError("expected exactly one encrypted-recovery rule group")
with open(sys.argv[2], "w", encoding="utf-8") as destination:
    yaml.safe_dump({"groups": selected}, destination, sort_keys=False)
PY

docker run --rm --user "$(id -u):$(id -g)" \
  -v "$temp_dir:/rules:ro" \
  --entrypoint /bin/promtool \
  "$PROMETHEUS_IMAGE" check rules /rules/choms-encrypted-recovery.rules.yaml
