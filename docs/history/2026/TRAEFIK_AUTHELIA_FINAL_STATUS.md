# Traefik + Authelia Final Status

Status: **Completed**

## Purpose

Traefik and Authelia provide the main external access and authentication layer for CHOMS-HOMELAB.

Traefik handles routing and HTTPS.

Authelia protects internal dashboards and administrative services.

## Public Routes

These routes are intentionally public and do not require Authelia:

- `https://chomsmaster.com`
- `https://www.chomsmaster.com`

## Authentication Portal

- `https://auth.chomsmaster.com`

## Protected by Authelia

- `https://home.chomsmaster.com`
- `https://grafana.chomsmaster.com`
- `https://kuma.chomsmaster.com`
- `https://traefik.chomsmaster.com`

## Native Login Applications

These applications keep their own authentication flow:

- `https://cloud.chomsmaster.com`
- `https://jellyfin.chomsmaster.com`

## Operational Commands

```bash
choms compose ps
choms compose logs traefik --tail=100
choms compose logs authelia --tail=100
choms compose restart traefik
choms compose restart authelia
choms health
choms status
```

## Operating Rules

- Public website must remain outside Authelia.
- Internal dashboards must remain protected by Authelia.
- Nextcloud and Jellyfin use native login.
- Use `choms compose` instead of manually typing long Compose commands.
- Do not expose administrative services directly without authentication.

## Final State

Traefik and Authelia are considered complete for Phase 1.

Future improvements belong to Phase 2+:

- stronger MFA policy
- central secrets management
- automated route validation
- certificate expiry alerts
- CI checks for router labels
