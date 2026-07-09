#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f ".env" ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

docker compose -f compose.yaml config >/tmp/choms-filebrowser-compose.out
docker compose -f compose.yaml up -d

echo
echo "Filebrowser deployed."
docker ps --filter "name=choms-filebrowser"
