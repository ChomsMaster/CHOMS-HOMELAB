#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f ".env" ]]; then
  echo "ERROR: missing .env file. Copy .env.example to .env first."
  exit 1
fi

docker compose -f compose.yaml config >/tmp/choms-postgres-compose.out
docker compose -f compose.yaml up -d

echo
echo "PostgreSQL deployed."
docker ps --filter "name=choms-postgres"
