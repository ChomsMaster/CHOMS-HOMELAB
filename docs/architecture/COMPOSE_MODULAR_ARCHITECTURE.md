# Docker Compose Modular Architecture

## Purpose

The CHOMS Docker Compose stack is modularized to avoid a single large monolithic Compose file.

This improves:

- readability
- maintainability
- service grouping
- future node separation
- operational clarity

## Active Structure

```text
docker/
├── compose.yml
└── compose/
    ├── core.yml
    ├── authelia.yml
    ├── monitoring.yml
    ├── cloud.yml
    ├── media.yml
    └── databases.yml
```

## Module Responsibilities

### `compose.yml`

Root Compose entry point.

### `compose/core.yml`

Core networking and public entry services:

- Traefik
- Nginx
- Pi-hole

### `compose/authelia.yml`

Authentication layer:

- Authelia
- ForwardAuth middleware

### `compose/monitoring.yml`

Observability stack:

- Grafana
- Prometheus
- Loki
- Promtail
- Uptime Kuma
- cAdvisor
- Node Exporter
- Scrutiny

### `compose/cloud.yml`

Cloud services:

- Nextcloud
- MariaDB

### `compose/media.yml`

Media services:

- Jellyfin

### `compose/databases.yml`

Database services:

- PostgreSQL

## Operational Wrapper

Use:

```bash
choms compose ps
choms compose config
choms compose up -d
```

Do not manually invoke the full Compose file chain unless debugging.

## Future Direction

In later phases, modules may map naturally to node roles:

- core node
- monitoring node
- apps node
- storage integration
- lab node
