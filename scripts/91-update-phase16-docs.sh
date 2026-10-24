#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="${CHOMS_BASE_DIR:-/data/projects/choms-homelab}"
cd "$BASE_DIR"

echo "Updating CHOMS documentation..."


cat > docs/inventory/SERVICES.md <<'DOC'
# CHOMS Services Inventory

| Service | Node | Status | Deploy |
|---|---|---|---|
| PostgreSQL | choms-node-02 | Running | choms deploy postgres |
| Redis | choms-node-02 | Running | choms deploy redis |

## Next Planned Services

- Filebrowser
- Nextcloud
- Portainer
- CHOMS Console
DOC

cat > docs/operations/DEPLOY.md <<'DOC'
# CHOMS Deploy Operations

## Source of Truth

Repository:

    /data/projects/choms-homelab

Runtime:

    /data/docker/stacks

## Deploy Flow

    Git
      ↓
    choms deploy <stack>
      ↓
    /data/docker/stacks
      ↓
    docker compose up -d

## Commands

List stacks:

    choms deploy

Deploy PostgreSQL:

    choms deploy postgres

Deploy Redis:

    choms deploy redis

Validate PostgreSQL:

    docker exec -it choms-postgres pg_isready -U choms -d choms_platform

Validate Redis:

    docker exec -it choms-redis redis-cli ping
DOC

echo "Documentation updated successfully."
