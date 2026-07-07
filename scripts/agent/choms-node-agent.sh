#!/usr/bin/env bash
set -euo pipefail

CONFIG="/opt/choms/node.yaml"
STATE_DIR="/var/lib/choms/agent"
STATE_FILE="$STATE_DIR/node-state.env"
LOG_FILE="/var/log/choms/choms-node-agent.log"

mkdir -p "$STATE_DIR" /var/log/choms

timestamp() {
  date --iso-8601=seconds
}

log() {
  echo "$(timestamp) $*" | tee -a "$LOG_FILE" >/dev/null
}

get_yaml_value() {
  local key="$1"
  grep -E "^${key}:" "$CONFIG" 2>/dev/null | head -1 | cut -d':' -f2- | sed 's/^ *//;s/ *$//;s/"//g'
}

if [[ ! -f "$CONFIG" ]]; then
  log "ERROR: missing node config: $CONFIG"
  exit 1
fi

NODE_ID="$(get_yaml_value node_id)"
ROLE="$(get_yaml_value role)"
SITE="$(get_yaml_value site)"
DOMAIN="$(get_yaml_value domain)"
HOSTNAME_NOW="$(hostname)"
IP_NOW="$(ip route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1)}' | head -1)"

if [[ -z "$IP_NOW" ]]; then
  IP_NOW="$(hostname -I | awk '{print $1}')"
fi

LAST_IP=""
LAST_HOSTNAME=""
LAST_ROLE=""

if [[ -f "$STATE_FILE" ]]; then
  source "$STATE_FILE"
fi

CHANGED="false"

if [[ "$IP_NOW" != "${LAST_IP:-}" ]]; then
  CHANGED="true"
fi

if [[ "$HOSTNAME_NOW" != "${LAST_HOSTNAME:-}" ]]; then
  CHANGED="true"
fi

if [[ "$ROLE" != "${LAST_ROLE:-}" ]]; then
  CHANGED="true"
fi

cat > "$STATE_FILE" <<STATE
LAST_NODE_ID="$NODE_ID"
LAST_HOSTNAME="$HOSTNAME_NOW"
LAST_ROLE="$ROLE"
LAST_IP="$IP_NOW"
LAST_SITE="$SITE"
LAST_DOMAIN="$DOMAIN"
LAST_CHECK="$(timestamp)"
STATE

if [[ "$CHANGED" == "true" ]]; then
  log "CHANGE node_id=$NODE_ID hostname=$HOSTNAME_NOW role=$ROLE ip=$IP_NOW site=$SITE domain=$DOMAIN"
else
  log "OK unchanged node_id=$NODE_ID hostname=$HOSTNAME_NOW role=$ROLE ip=$IP_NOW"
fi
