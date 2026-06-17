#!/bin/bash
set -e

echo "Updating system packages..."
sudo apt update
sudo apt upgrade -y

echo "Updating Docker images..."

for dir in /opt/choms/docker/*; do
  if [ -f "$dir/compose.yml" ]; then
    echo "Updating stack: $dir"
    cd "$dir"
    docker compose pull
    docker compose up -d
  fi
done

echo "Cleaning unused Docker resources..."
docker system prune -f

echo "System update completed."
