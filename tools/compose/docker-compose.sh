#!/bin/bash
set -euo pipefail

cd /data/projects/choms-homelab/docker

exec docker compose \
  -f compose.yml \
  -f compose/core.yml \
  -f compose/authelia.yml \
  -f compose/monitoring.yml \
  -f compose/cloud.yml \
  -f compose/media.yml \
  -f compose/databases.yml \
  "$@"
