#!/usr/bin/env bash

set -euo pipefail
set +x

namespace="monitoring"
secret_name="choms-monitoring-alertmanager-config"
token_mount="/etc/alertmanager/secrets/${secret_name}/telegram-bot-token"
KUBE_HOST="${KUBE_HOST:-chomsmaster@192.168.1.138}"
ssh_config="${CHOMS_SSH_CONFIG:-/dev/null}"

for command_name in ssh python3; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "ERROR: ${command_name} is required" >&2
    exit 1
  fi
done

remote_context="$(ssh -F "$ssh_config" "$KUBE_HOST" 'kubectl config current-context')"
echo "Remote Kubernetes context: ${remote_context}"

ssh -F "$ssh_config" "$KUBE_HOST" "kubectl get namespace ${namespace} >/dev/null"

for verb in create patch; do
  if [[ "$(ssh -F "$ssh_config" "$KUBE_HOST" "kubectl auth can-i ${verb} secrets -n ${namespace}")" != "yes" ]]; then
    echo "ERROR: remote Kubernetes identity cannot ${verb} Secrets in ${namespace}" >&2
    exit 1
  fi
done

IFS= read -r -p "Continue and reconcile ${namespace}/${secret_name}? Type yes: " confirmation
if [[ "$confirmation" != "yes" ]]; then
  echo "Cancelled."
  exit 0
fi
unset confirmation

umask 077
temp_dir="$(mktemp -d)"
config_file="${temp_dir}/alertmanager.yaml"
token_file="${temp_dir}/telegram-bot-token"
manifest_file="${temp_dir}/secret.json"

cleanup() {
  unset bot_token chat_id
  rm -f -- "$config_file" "$token_file" "$manifest_file"
  if [[ -d "$temp_dir" ]]; then
    rmdir -- "$temp_dir"
  fi
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

IFS= read -r -s -p "Telegram bot token: " bot_token
printf '\n' >&2

if [[ ! "$bot_token" =~ ^[0-9]{6,12}:[A-Za-z0-9_-]{30,64}$ ]]; then
  echo "ERROR: invalid Telegram bot token format" >&2
  exit 1
fi

IFS= read -r -s -p "Telegram chat_id: " chat_id
printf '\n' >&2

if [[ ! "$chat_id" =~ ^-?[0-9]+$ ]] || [[ "$chat_id" == "0" ]]; then
  echo "ERROR: chat_id must be a non-zero integer" >&2
  exit 1
fi

cat >"$config_file" <<EOF
global:
  resolve_timeout: 5m

route:
  receiver: "null"
  group_by:
    - alertname
    - namespace
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - receiver: "null"
      matchers:
        - alertname="Watchdog"
    - receiver: telegram
      matchers:
        - severity="critical"

receivers:
  - name: "null"
  - name: telegram
    telegram_configs:
      - bot_token_file: ${token_mount}
        chat_id: ${chat_id}
        send_resolved: true
        parse_mode: HTML
        message: >-
          {{ if eq .Status "firing" }}🔥{{ else }}✅{{ end }}
          <b>{{ .Status | toUpper }}</b> —
          {{ .CommonLabels.alertname | html }}{{ if .CommonLabels.namespace }}
          · {{ .CommonLabels.namespace | html }}{{ end }}{{ if .CommonAnnotations.summary }}
          — {{ .CommonAnnotations.summary | html }}{{ end }}
EOF

printf '%s' "$bot_token" >"$token_file"
chmod 0600 "$config_file" "$token_file"

python3 - "$namespace" "$secret_name" "$config_file" "$token_file" \
  >"$manifest_file" <<'PY'
import base64
import json
import sys

namespace, secret_name, config_path, token_path = sys.argv[1:]

with open(config_path, "rb") as config_stream:
    config = base64.b64encode(config_stream.read()).decode("ascii")
with open(token_path, "rb") as token_stream:
    token = base64.b64encode(token_stream.read()).decode("ascii")

json.dump(
    {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": secret_name, "namespace": namespace},
        "type": "Opaque",
        "data": {
            "alertmanager.yaml": config,
            "telegram-bot-token": token,
        },
    },
    sys.stdout,
)
PY
chmod 0600 "$manifest_file"

unset bot_token chat_id

ssh -F "$ssh_config" "$KUBE_HOST" \
  'kubectl apply --server-side --field-manager=choms-alertmanager-telegram-bootstrap -f - >/dev/null' \
  <"$manifest_file"

echo "Alertmanager Telegram Secret reconciled in ${namespace}."
