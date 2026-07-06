# CHOMS Project Status

## Current Phase

Phase 16 — Core Platform Foundation

## Source of Truth

Repository:

    /data/projects/CHOMS-HOMELAB

Runtime:

    /data/docker

Rule:

    Edit Git. Deploy to runtime. Do not manually maintain runtime as source.

## Deployment Flow

    Git repository
        ↓
    stacks/
        ↓
    choms deploy <stack>
        ↓
    /data/docker/stacks/
        ↓
    docker compose up -d

## Nodes

- choms-node-01 — Edge
- choms-node-02 — Application
- choms-nas — Storage

## Completed

- Node standard bootstrap
- Application node bootstrap
- GitHub SSH access on node-02
- Platform inventory command
- Docker networks:
  - choms-public
  - choms-backend
  - choms-database
- PostgreSQL stack
- Redis stack
- CHOMS deploy command
- qBittorrent NAS mount issue corrected

## Running on Node-02

- choms-postgres
- choms-redis

## Critical Rules

Never edit as source:

    /data/docker

Always edit source in:

    /data/projects/CHOMS-HOMELAB

Deploy using:

    choms deploy <stack>

## Next Task

Continue building managed stacks. Candidate next stacks:

- Nextcloud
- Filebrowser
- Portainer
- CHOMS Console
