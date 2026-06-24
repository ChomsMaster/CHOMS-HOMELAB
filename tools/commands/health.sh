#!/bin/bash
set -euo pipefail

echo "CHOMS HEALTH"
echo "============"

check_cmd() {
  name="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    echo "✅ $name"
  else
    echo "❌ $name"
  fi
}

check_cmd "Docker" docker info
check_cmd "Compose config" /data/projects/choms-homelab/tools/commands/compose.sh config
check_cmd "Traefik" docker inspect -f '{{.State.Running}}' choms-traefik
check_cmd "Authelia" docker inspect -f '{{.State.Running}}' choms-authelia
check_cmd "Nginx" docker inspect -f '{{.State.Running}}' choms-nginx
check_cmd "Postgres" docker inspect -f '{{.State.Running}}' choms-postgres
check_cmd "UFW" systemctl is-active ufw
check_cmd "WireGuard" ip link show wg0
check_cmd "Internet DNS" getent hosts cloudflare.com

echo
echo "Quick status complete."
