#!/bin/bash
set -e

echo "Updating system packages..."
apt update
apt upgrade -y

echo "Updating Docker images..."
cd /data/projects/choms-homelab/docker
docker compose pull
docker compose up -d

echo "Cleaning unused Docker resources..."
docker system prune -f

echo "System update completed."
