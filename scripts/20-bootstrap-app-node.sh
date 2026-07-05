#!/usr/bin/env bash
set -euo pipefail

CHOMS_USER="${CHOMS_USER:-chomsmaster}"

echo "========================================"
echo " CHOMS Platform - Application Node"
echo "========================================"

if [[ $EUID -ne 0 ]]; then
  echo "ERROR: run with sudo."
  exit 1
fi

mkdir -p \
  /data/compose/{postgres,mariadb,nextcloud,redis,apps,shiftcore} \
  /data/docker/{postgres,mariadb,nextcloud,redis,apps,shiftcore} \
  /data/config/{postgres,mariadb,nextcloud,redis,apps,shiftcore} \
  /data/logs/{postgres,mariadb,nextcloud,apps,shiftcore} \
  /data/backups/{postgres,mariadb,nextcloud,apps,shiftcore}

if id "$CHOMS_USER" >/dev/null 2>&1; then
  chown -R "$CHOMS_USER:$CHOMS_USER" \
    /data/compose \
    /data/docker \
    /data/config \
    /data/logs \
    /data/backups
fi

echo
echo "Application node directories:"
find /data -maxdepth 2 -type d | sort

echo
echo "CHOMS Application Node ready."
