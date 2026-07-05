#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo " CHOMS Compute Node Bootstrap"
echo "========================================"
echo

if [[ $EUID -ne 0 ]]; then
  echo "ERROR: run with sudo."
  exit 1
fi

if ! grep -qi debian /etc/os-release; then
  echo "ERROR: this bootstrap currently supports Debian only."
  exit 1
fi

echo "[1/6] Installing base packages..."
apt update
apt install -y \
  curl \
  wget \
  git \
  htop \
  vim \
  ufw \
  nfs-common \
  cifs-utils \
  ca-certificates \
  gnupg

echo "[2/6] Creating base directories..."
mkdir -p /data
mkdir -p /mnt/choms-media
mkdir -p /mnt/choms-storage

echo "[3/6] Installing Docker..."
install -m 0755 -d /etc/apt/keyrings

if [[ ! -f /etc/apt/keyrings/docker.gpg ]]; then
  curl -fsSL https://download.docker.com/linux/debian/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
fi

. /etc/os-release

cat > /etc/apt/sources.list.d/docker.list <<DOCKER_REPO
deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian ${VERSION_CODENAME} stable
DOCKER_REPO

apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable --now docker

echo "[4/6] Adding operational user to docker group..."
if id chomsmaster >/dev/null 2>&1; then
  usermod -aG docker chomsmaster
else
  echo "WARNING: user chomsmaster not found. Skipping docker group assignment."
fi

echo "[5/6] Applying basic firewall baseline..."
ufw allow OpenSSH
ufw --force enable

echo "[6/6] Validation..."
hostname
docker --version
docker compose version
ufw status

echo
echo "Bootstrap completed."
echo "IMPORTANT: log out and log back in for docker group permissions to apply."

chmod +x scripts/bootstrap-compute-node.sh
