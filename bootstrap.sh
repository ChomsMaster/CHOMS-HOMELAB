#!/bin/bash

set -euo pipefail

LOGFILE="/tmp/choms-bootstrap.log"

exec > >(tee -a "$LOGFILE")
exec 2>&1

clear

echo "=============================================="
echo "      CHOMS-HOMELAB Bootstrap Installer"
echo "=============================================="
echo

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: Execute with sudo."
    exit 1
fi

if ! grep -qi debian /etc/os-release; then
    echo "ERROR: This installer only supports Debian."
    exit 1
fi

if ! ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo "ERROR: No Internet connection."
    exit 1
fi

echo "System validation OK."
echo

STEPS=(
"01-install-base-tools.sh"
"02-create-server-structure.sh"
"03-install-docker.sh"
"04-setup-firewall.sh"
"05-setup-storage.sh"
"06-install-wireguard.sh"
"07-deploy-nginx.sh"
"08-deploy-postgresql.sh"
"09-deploy-pihole.sh"
)

TOTAL=${#STEPS[@]}
CURRENT=1

chmod +x scripts/*.sh

for STEP in "${STEPS[@]}"; do

    echo
    echo "[$CURRENT/$TOTAL] Running $STEP"

    "./scripts/$STEP"

    echo "Completed."

    CURRENT=$((CURRENT+1))

done

echo
echo "=============================================="
echo "Bootstrap completed successfully."
echo
echo "Log:"
echo "$LOGFILE"
echo "=============================================="

