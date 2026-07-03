#!/usr/bin/env bash
set -euo pipefail

CHOMS_USER="${CHOMS_USER:-chomsmaster}"

echo "========================================"
echo " CHOMS Platform - Node Standard"
echo "========================================"

if [[ $EUID -ne 0 ]]; then
  echo "ERROR: run with sudo."
  exit 1
fi

echo "[1/5] Installing base packages..."
apt update
apt install -y \
  curl wget git htop vim ufw \
  nfs-common cifs-utils \
  ca-certificates gnupg

echo "[2/5] Creating CHOMS directory standard..."
mkdir -p \
  /data/projects \
  /data/docker \
  /data/backups \
  /data/tmp \
  /data/logs \
  /data/config \
  /data/scripts \
  /data/cache \
  /mnt/choms-media \
  /mnt/choms-storage \
  /mnt/choms-backups \
  /opt/choms

echo "[3/5] Applying ownership..."
if id "$CHOMS_USER" >/dev/null 2>&1; then
  chown -R "$CHOMS_USER:$CHOMS_USER" \
    /data/projects \
    /data/docker \
    /data/backups \
    /data/tmp \
    /data/logs \
    /data/config \
    /data/scripts \
    /data/cache
else
  echo "WARNING: user $CHOMS_USER not found. Ownership skipped."
fi

echo "[4/5] Applying firewall baseline..."
ufw allow OpenSSH
ufw --force enable

echo "[5/5] Validation..."
echo
hostname
echo
ls -ld \
  /data/projects \
  /data/docker \
  /data/backups \
  /data/tmp \
  /data/logs \
  /data/config \
  /data/scripts \
  /data/cache \
  /mnt/choms-media \
  /mnt/choms-storage \
  /mnt/choms-backups \
  /opt/choms
echo
ufw status

echo
echo "CHOMS node standard applied."
