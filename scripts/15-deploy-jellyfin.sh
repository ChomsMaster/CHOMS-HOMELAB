#!/bin/bash

set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker is not installed."
    exit 1
fi

mkdir -p /data/docker/jellyfin/config
mkdir -p /data/docker/jellyfin/cache
mkdir -p /data/media/peliculas
mkdir -p /data/media/series
mkdir -p /data/media/musica

cd /data/projects/choms-homelab/docker

docker compose config >/dev/null
docker compose up -d jellyfin

docker ps | grep jellyfin

echo "Jellyfin deployed."
