# CHOMS-HOMELAB System Overview

## Purpose

CHOMS-HOMELAB is a production-inspired self-hosted infrastructure platform.

It is designed to be:

- practical
- documented
- version-controlled
- reproducible
- secure by default
- ready to evolve into a multi-node platform

## Current Architecture

```mermaid
flowchart TD
    Internet((Internet))
    Router[ISP Router]
    Traefik[Traefik Reverse Proxy]
    Authelia[Authelia]
    Docker[Docker Compose Stack]

    PublicWeb[Public Website]
    Home[Home Portal]
    Grafana[Grafana]
    Kuma[Uptime Kuma]
    Cloud[Nextcloud]
    Media[Jellyfin]
    Monitoring[Monitoring Stack]
    Databases[PostgreSQL / MariaDB]
    DNS[Pi-hole]
    VPN[WireGuard]
    CLI[CHOMS CLI]

    Internet --> Router
    Router --> Traefik
    Traefik --> PublicWeb
    Traefik --> Authelia
    Authelia --> Home
    Authelia --> Grafana
    Authelia --> Kuma
    Traefik --> Cloud
    Traefik --> Media
    Docker --> Monitoring
    Docker --> Databases
    Docker --> DNS
    VPN --> Docker
    CLI --> Docker
```

## Current Host Role

The current server acts as the first CHOMS node.

Current responsibilities:

- reverse proxy
- authentication
- public website
- application hosting
- monitoring
- database hosting
- DNS filtering
- VPN endpoint
- operational control

## Public and Private Access Model

### Public

- `chomsmaster.com`
- `www.chomsmaster.com`

### Authentication

- `auth.chomsmaster.com`

### Protected

- `home.chomsmaster.com`
- `grafana.chomsmaster.com`
- `kuma.chomsmaster.com`
- `traefik.chomsmaster.com`

### Native Login

- `cloud.chomsmaster.com`
- `jellyfin.chomsmaster.com`

## Operational Model

Primary operational command:

```bash
choms
```

Key commands:

```bash
choms health
choms status
choms version
choms urls
choms compose ps
choms service list
choms logs <service>
choms restart <service>
choms update
choms vault list
```

## Storage Model

Current storage is local to the host.

Planned Phase 2 storage model:

```mermaid
flowchart TD
    Mini1[Mini PC Core Node]
    Mini2[Future Apps Node]
    Mini3[Future Monitoring Node]
    NAS[Future NAS / CHOMS Storage]
    Backups[Backups and Snapshots]

    Mini1 --> NAS
    Mini2 --> NAS
    Mini3 --> NAS
    NAS --> Backups
```

The future architecture will separate:

- compute nodes
- storage
- backups
- monitoring

## Future Architecture Direction

CHOMS is expected to evolve toward:

- dedicated NAS
- 3–4 mini PC nodes
- managed switch
- OPNsense / pfSense firewall
- VLAN segmentation
- backup and restore automation
- CI/CD
- K3s evaluation
- service placement strategy

## Current Phase

Phase 1 is complete.

Next phase:

**Phase 2 — Backups, resilience and recovery**
