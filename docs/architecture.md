# CHOMS-HOMELAB Architecture

## Current model

CHOMS-HOMELAB is currently a single-node Docker-based homelab using Traefik as the public reverse proxy.

## Core components

- Traefik: HTTPS entrypoint and reverse proxy
- Authelia: Authentication layer for private services
- Nginx/Home: Homelab dashboard
- Nextcloud: Personal cloud
- Jellyfin: Media server
- Grafana/Prometheus/Loki/Uptime Kuma: Monitoring and observability

## Cluster-ready direction

The project is being structured to support future multi-node growth.

Key principles:

- One subdomain per service
- Data kept outside Git
- Secrets excluded from repository
- Modular Docker Compose files
- Clear separation between public, private, and VPN-only services
- Stateful and stateless services documented separately
