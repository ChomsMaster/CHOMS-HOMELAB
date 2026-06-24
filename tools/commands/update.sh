#!/bin/bash
set -euo pipefail

BASE="/data/projects/choms-homelab"

echo "========================================"
echo " CHOMS Update"
echo "========================================"
echo

cd "$BASE"

echo "[1/3] Updating Git..."
git pull

echo
echo "[2/3] Pulling Docker images..."
"$BASE/tools/compose/docker-compose.sh" pull

echo
echo "[3/3] Applying updates..."
"$BASE/tools/compose/docker-compose.sh" up -d

echo
echo "========================================"
echo " Update completed successfully."
echo "========================================"
