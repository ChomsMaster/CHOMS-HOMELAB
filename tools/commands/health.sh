#!/bin/bash
set -euo pipefail

BASE_DIR="${CHOMS_BASE_DIR:-/data/projects/choms-homelab}"
PLATFORM_CONFIG="$BASE_DIR/config/platform/nodes.env"

if [[ ! -f "$PLATFORM_CONFIG" ]]; then
  echo "ERROR: platform config not found: $PLATFORM_CONFIG"
  exit 1
fi

# shellcheck disable=SC1090
source "$PLATFORM_CONFIG"

echo "CHOMS HEALTH"
echo "============"

check_cmd() {
  local name="$1"
  shift

  if "$@" >/dev/null 2>&1; then
    echo "✅ $name"
  else
    echo "❌ $name"
  fi
}

check_remote_container_health() {
  local container="$1"

  ssh \
    -o BatchMode=yes \
    -o ConnectTimeout=3 \
    "chomsmaster@${CHOMS_APPLICATION_IP}" \
    "docker inspect -f '{{.State.Health.Status}}' '$container' | grep -qx healthy"
}

check_cmd "Docker" docker info
check_cmd "Compose config" "$BASE_DIR/tools/commands/compose.sh" config

check_cmd "Authelia node-01" \
  docker inspect -f '{{.State.Running}}' choms-authelia

check_cmd "Nginx node-01" \
  docker inspect -f '{{.State.Running}}' choms-nginx

check_cmd "Node-02 SSH" \
  ssh \
    -o BatchMode=yes \
    -o ConnectTimeout=3 \
    "chomsmaster@${CHOMS_APPLICATION_IP}" \
    true

check_cmd "Postgres node-02" \
  check_remote_container_health choms-postgres

check_cmd "Jellyfin node-02" \
  check_remote_container_health choms-jellyfin-node02

check_cmd "UFW" systemctl is-active ufw
check_cmd "WireGuard" ip link show wg0
check_cmd "Internet DNS" getent hosts cloudflare.com

echo
echo "Quick status complete."
