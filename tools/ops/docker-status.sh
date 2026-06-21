#!/bin/bash

set -euo pipefail

echo "=============================================="
echo " CHOMS-HOMELAB Docker Status"
echo "=============================================="
echo

echo "===== Running Containers ====="
docker ps

echo
echo "===== Compose Services ====="
cd /data/projects/choms-homelab/docker
docker compose ps
