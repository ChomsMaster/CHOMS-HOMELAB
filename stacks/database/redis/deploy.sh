#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f ".env" ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

docker compose -f compose.yaml config >/tmp/choms-redis-compose.out
docker compose -f compose.yaml up -d

echo
echo "Redis deployed."
docker ps --filter "name=choms-redis"
