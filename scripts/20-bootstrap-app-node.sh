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

echo
echo "[1/6] Installing base packages..."

apt update
apt install -y \
  curl \
  wget \
  git \
  htop \
  vim \
  tree \
  rsync \
  ufw \
  nfs-common \
  cifs-utils \
  ca-certificates \
  gnupg

echo
echo "[2/6] Creating application node base directories..."

mkdir -p \
  /data/compose/{postgres,mariadb,nextcloud,redis,applications,shiftcore} \
  /data/docker/{postgres,mariadb,nextcloud,redis,applications,shiftcore,configs,secrets,volumes,networks,stacks} \
  /data/config/{postgres,mariadb,nextcloud,redis,applications,shiftcore} \
  /data/logs/{postgres,mariadb,nextcloud,applications,shiftcore} \
  /data/backups/{postgres,mariadb,nextcloud,applications,shiftcore}

echo
echo "[3/6] Creating stack directory layout..."

mkdir -p \
  /data/docker/stacks/database/{postgres,redis} \
  /data/docker/stacks/applications/{nextcloud,shiftcore} \
  /data/docker/stacks/monitoring \
  /data/docker/stacks/storage \
  /data/docker/stacks/testing

echo
echo "[4/6] Creating CHOMS Docker networks if missing..."

docker network inspect choms-public >/dev/null 2>&1 || docker network create choms-public
docker network inspect choms-backend >/dev/null 2>&1 || docker network create choms-backend
docker network inspect choms-database >/dev/null 2>&1 || docker network create choms-database

echo
echo "[5/6] Applying ownership..."

if id "$CHOMS_USER" >/dev/null 2>&1; then
  chown -R "$CHOMS_USER:$CHOMS_USER" \
    /data/compose \
    /data/docker \
    /data/config \
    /data/logs \
    /data/backups
else
  echo "WARNING: user $CHOMS_USER not found. Ownership skipped."
fi

echo
echo "[6/6] Validation..."

echo
echo "Docker networks:"
docker network ls | grep choms || true

echo
echo "Application stack layout:"
tree -a -L 3 /data/docker/stacks || find /data/docker/stacks -maxdepth 3 -type d | sort

echo
echo "CHOMS Application Node ready."
