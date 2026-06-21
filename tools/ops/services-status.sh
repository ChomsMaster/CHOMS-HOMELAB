#!/bin/bash

set -euo pipefail

echo "=============================================="
echo " CHOMS-HOMELAB Services Status"
echo "=============================================="
echo

for service in smbd minidlna choms-backup.timer wg-quick@wg0 fail2ban; do
    printf "%-25s " "$service"
    systemctl is-active "$service" || true
done
