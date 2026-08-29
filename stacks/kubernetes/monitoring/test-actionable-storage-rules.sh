#!/usr/bin/env bash

set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VALUES="$ROOT/values.yaml"
TESTS="$ROOT/tests/choms-actionable-storage.test.yaml"
PROMETHEUS_IMAGE='quay.io/prometheus/prometheus@sha256:64f71bb84e03c855948418b0fc5dea53e9543d8e3fc9931598f583805507f05e'

umask 077
temp_dir="$(mktemp -d)"
cleanup() { rm -rf -- "$temp_dir"; }
trap cleanup EXIT HUP INT TERM

python3 - "$VALUES" "$temp_dir/choms-actionable-storage.rules.yaml" <<'PY'
import sys
import yaml

with open(sys.argv[1], encoding="utf-8") as source:
    values = yaml.safe_load(source)
groups = values["additionalPrometheusRulesMap"]["choms-actionable-storage"]["groups"]
with open(sys.argv[2], "w", encoding="utf-8") as destination:
    yaml.safe_dump({"groups": groups}, destination, sort_keys=False)
PY
cp "$TESTS" "$temp_dir/"

docker run --rm --user "$(id -u):$(id -g)" \
  -v "$temp_dir:/rules:ro" \
  --entrypoint /bin/promtool \
  "$PROMETHEUS_IMAGE" check rules /rules/choms-actionable-storage.rules.yaml
docker run --rm --user "$(id -u):$(id -g)" \
  -v "$temp_dir:/rules:ro" \
  --entrypoint /bin/promtool \
  "$PROMETHEUS_IMAGE" test rules /rules/choms-actionable-storage.test.yaml
