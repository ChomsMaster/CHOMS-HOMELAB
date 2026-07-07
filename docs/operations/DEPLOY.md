# CHOMS Deploy Operations

## Source of Truth

Repository:

    /data/projects/CHOMS-HOMELAB

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
