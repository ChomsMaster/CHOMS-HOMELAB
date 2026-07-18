#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="${CHOMS_BASE_DIR:-/data/projects/choms-homelab}"

cd "$BASE_DIR"

mkdir -p \
  docs/architecture/ADR \
  docs/operations \
  docs/inventory

cat > AI_HANDOFF.md <<'DOC'
# CHOMS AI Handoff

When continuing CHOMS in a new chat:

1. Read this file first.
2. Read PROJECT_STATUS.md.
3. Read CHANGELOG.md.
4. Read docs/architecture/DEPLOYMENT_MODEL.md.
5. Read docs/architecture/ADR.

Rules:

- Do not redesign existing architecture unless explicitly requested.
- Do not edit runtime files as source.
- Git repository is the source of truth.
- Runtime directories are generated/deployed artifacts.
- Continue from the current phase and next task.
- If an architectural decision changes, create or update an ADR.
DOC

cat > PROJECT_STATUS.md <<'DOC'
# CHOMS Project Status

## Current Phase

Phase 16 — Core Platform Foundation

## Source of Truth

Repository:

    /data/projects/choms-homelab

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

    /data/projects/choms-homelab

Deploy using:

    choms deploy <stack>

## Next Task

Continue building managed stacks. Candidate next stacks:

- Nextcloud
- Filebrowser
- Portainer
- CHOMS Console
DOC

cat > ROADMAP.md <<'DOC'
# CHOMS Roadmap

## Current

- Stabilize Application Node
- Standardize Git → Runtime deployment
- Move core services into managed stacks

## Short Term

- Add Nextcloud stack
- Add Filebrowser stack
- Add Portainer stack
- Improve choms deploy
- Add health checks to deploy flow
- Add service inventory docs

## Mid Term

- Add CHOMS Console
- Add dashboard/kiosk mode
- Add backup/restore automation
- Add secrets management
- Add multi-node deploy support

## Long Term

- Add Compute Node
- Add Windows Repair Lab VM
- Add orchestration layer
- Add AI-assisted repair/documentation tools
DOC

cat > CHANGELOG.md <<'DOC'
# CHOMS Changelog

## 2026-07-06

### Added

- Application Node bootstrap
- PostgreSQL stack
- Redis stack
- CHOMS deploy command
- Project documentation structure
- AI handoff document

### Changed

- Git repository is now the source of truth.
- Runtime directory is treated as generated deployment output.

### Fixed

- qBittorrent was incorrectly using NAS system SSD paths.
- qBittorrent now mounts:
  - /downloads → /srv/storage/downloads/torrents
  - /config → /srv/storage/docker/qbittorrent/config
  - /logs → /srv/storage/logs
  - /movies → /srv/media/Movies
  - /series → /srv/media/Series

### Current State

- Node-02 runs PostgreSQL and Redis.
- Deployment engine v1 is working.
DOC

cat > docs/architecture/DEPLOYMENT_MODEL.md <<'DOC'
# CHOMS Deployment Model

## Principle

The Git repository is the Single Source of Truth.

Runtime directories must not be edited as source.

## Repository

    /data/projects/choms-homelab

Contains:

- stacks
- scripts
- tools
- docs
- configuration templates

## Runtime

    /data/docker

Contains deployed runtime artifacts.

Runtime may contain local `.env` files that are not versioned.

## Deployment Flow

    Git
      ↓
    stacks/<domain>/<stack>
      ↓
    choms deploy <stack>
      ↓
    /data/docker/stacks/<domain>/<stack>
      ↓
    docker compose up -d

## Environment Files

Versioned:

    .env.example

Runtime-only:

    .env

The deploy command must not overwrite `.env`.

## Rule

Do not manually maintain files inside `/data/docker/stacks` as source.
DOC

cat > docs/architecture/NODE_ROLES.md <<'DOC'
# CHOMS Node Roles

## Edge Node

Host:

    choms-node-01

Responsibilities:

- Reverse proxy
- VPN
- DDNS
- Authentication
- Monitoring frontend
- DNS services

## Application Node

Host:

    choms-node-02

Responsibilities:

- PostgreSQL
- Redis
- Nextcloud
- ShiftCore
- Application services
- Worker services

## Storage Node

Host:

    choms-nas

Responsibilities:

- RAID storage
- NFS
- Samba
- Media storage
- Backups
- File services
DOC

cat > docs/architecture/STORAGE_LAYOUT.md <<'DOC'
# CHOMS Storage Layout

## NAS

System SSD:

    120 GB

Storage RAID:

    /srv/storage
    RAID0 2 x 3 TB
    Approx usable: 5.5 TB

Media RAID:

    /srv/media
    RAID0 2 x 2 TB
    Approx usable: 3.6 TB

## Important Warning

Current NAS arrays are RAID0.

RAID0 provides capacity and speed but no disk redundancy.

Backups are mandatory for important data.

## qBittorrent

Correct runtime paths:

    /srv/storage/docker/qbittorrent/config
    /srv/storage/downloads/torrents
    /srv/storage/logs

Media output:

    /srv/media/Movies
    /srv/media/Series
DOC

cat > docs/architecture/NETWORK_TOPOLOGY.md <<'DOC'
# CHOMS Network Topology

## Nodes

- choms-node-01 — 192.168.1.138
- choms-node-02 — 192.168.1.172
- choms-nas — 192.168.1.167

## Docker Networks

- choms-public
- choms-backend
- choms-database

## Domain

    chomsmaster.com

## DDNS

Namecheap DDNS is configured on the Edge Node.

Managed records:

- @
- *
DOC

cat > docs/architecture/ADR/ADR-0001-Git-Source-Of-Truth.md <<'DOC'
# ADR-0001 — Git Is the Source of Truth

## Status

Accepted

## Context

Stacks were initially created directly under `/data/docker/stacks`.

That made runtime files drift away from Git and caused unclear ownership.

## Decision

The Git repository is the Single Source of Truth.

Stacks must be edited in:

    /data/projects/choms-homelab/stacks

Runtime is generated into:

    /data/docker/stacks

## Consequences

- Runtime files are not authoritative.
- `.env` files remain runtime-specific.
- Deployments must use `choms deploy <stack>`.
DOC

cat > docs/architecture/ADR/ADR-0002-Node-Roles.md <<'DOC'
# ADR-0002 — Node Roles

## Status

Accepted

## Decision

CHOMS uses role-based nodes:

- Edge
- Application
- Storage
- Future: Compute

## Consequences

Services are placed by responsibility, not randomly by host.

This enables future scaling by adding nodes.
DOC

cat > docs/architecture/ADR/ADR-0003-Deployment-Engine.md <<'DOC'
# ADR-0003 — CHOMS Deploy Engine

## Status

Accepted

## Context

Manual Docker Compose operations do not scale well across nodes and services.

## Decision

Create `choms deploy <stack>`.

The command:

1. Finds the stack in Git.
2. Copies it to runtime.
3. Preserves `.env`.
4. Validates Docker Compose.
5. Runs `docker compose up -d`.

## Current Limitations

- No rollback.
- No remote multi-node execution.
- No audit log.
- No automatic health enforcement beyond Docker healthchecks.
DOC

cat > docs/operations/DEPLOY.md <<'DOC'
# CHOMS Deploy Operations

## List Available Stacks

    choms deploy

## Deploy Redis

    choms deploy redis

## Deploy PostgreSQL

    choms deploy postgres

## Verify PostgreSQL

    docker exec -it choms-postgres pg_isready -U choms -d choms_platform

## Verify Redis

    docker exec -it choms-redis redis-cli ping
DOC

cat > docs/operations/BOOTSTRAP.md <<'DOC'
# CHOMS Bootstrap Operations

## Application Node

Run:

    sudo ./scripts/20-bootstrap-app-node.sh

This prepares:

- Base packages
- Docker stack directories
- CHOMS Docker networks
- Runtime structure
- Ownership
DOC

cat > docs/operations/TROUBLESHOOTING.md <<'DOC'
# CHOMS Troubleshooting

## qBittorrent Mount Issue

If qBittorrent shows `/downloads` mounted on `/dev/sda2`, it is using the NAS system SSD incorrectly.

Correct state:

    /downloads -> /dev/md0
    /config    -> /dev/md0
    /logs      -> /dev/md0
    /movies    -> /dev/md1
    /series    -> /dev/md1

Check:

    docker exec qbittorrent df -h /downloads /config /logs /movies /series
DOC

cat > docs/inventory/NODES.md <<'DOC'
# CHOMS Nodes Inventory

## Edge

- Hostname: choms-node-01
- IP: 192.168.1.138
- Role: Edge

## Application

- Hostname: choms-node-02
- IP: 192.168.1.172
- Role: Application

## Storage

- Hostname: choms-nas
- IP: 192.168.1.167
- Role: Storage
DOC

cat > docs/inventory/SERVICES.md <<'DOC'
# CHOMS Services Inventory

## Node-02

- choms-postgres
- choms-redis

## NAS

- qbittorrent
- filebrowser
- nginx-proxy-manager
- uptime-kuma

## Node-01

- Traefik
- Authelia
- Pi-hole
- Grafana
- Prometheus
- Loki
- Jellyfin
DOC

cat > docs/inventory/STORAGE.md <<'DOC'
# CHOMS Storage Inventory

## NAS

    /srv/storage
    /srv/media

## Node-01

- M.2 120 GB
- SSD 960 GB
- USB SSD 240 GB

## Node-02

- NVMe 1 TB
- SATA 2.5 HDD 1 TB
DOC

echo "CHOMS project documentation generated."
