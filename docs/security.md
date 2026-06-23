# CHOMS-HOMELAB Security Policy

## Public services

These services are intentionally reachable from the public Internet:

- `www.chomsmaster.com` - Public website / portfolio
- `cloud.chomsmaster.com` - Nextcloud, protected by Nextcloud authentication
- `jellyfin.chomsmaster.com` - Jellyfin, protected by Jellyfin authentication

## Authelia-protected services

These services must be protected by Authelia:

- `home.chomsmaster.com`
- `grafana.chomsmaster.com`
- `kuma.chomsmaster.com`
- `traefik.chomsmaster.com`
- `vault.chomsmaster.com`
- `git.chomsmaster.com`
- `photos.chomsmaster.com`
- `n8n.chomsmaster.com`

## VPN-only services

These services must not be exposed directly to the Internet:

- SSH
- PostgreSQL
- MariaDB
- Internal databases
- Pi-hole admin
- Raw monitoring endpoints
- Internal Docker services

## Current authentication strategy

- Traefik is the public reverse proxy.
- Authelia is the central authentication layer for private dashboards.
- Public services keep their own native authentication.
- Direct public service ports should remain closed unless explicitly required.
