# CHOMS-HOMELAB Project Status

## Current State

Current phase: **Phase 1 completed**  
Current tag: **v1.0.0-phase1**  
Next phase: **Phase 2 — Backups, resilience and recovery**

## Executive Summary

CHOMS-HOMELAB has completed its foundation infrastructure phase.

The platform currently provides a working self-hosted environment with:

- Debian 13 host
- Docker and modular Docker Compose
- Traefik reverse proxy
- Let's Encrypt HTTPS
- Authelia authentication layer
- Public website
- Protected internal services
- Monitoring stack
- WireGuard VPN
- Firewall and intrusion protection
- Custom operational CLI
- GitHub-based documentation and versioning

## Phase 1 Status

| Capability | Status |
|---|---|
| Debian host | Completed |
| Docker runtime | Completed |
| Docker Compose modularization | Completed |
| Traefik routing | Completed |
| HTTPS certificates | Completed |
| Authelia authentication | Completed |
| Public website | Completed |
| Monitoring stack | Completed |
| WireGuard | Completed |
| UFW / Fail2ban | Completed |
| CHOMS CLI | Completed |
| CHOMS Doctor / Health | Completed |
| Repository documentation baseline | Completed |
| Phase 1 release tag | Completed |

## Current Operational Validation

Use:

```bash
choms health
choms status
choms compose config
choms compose ps
```

Expected:

- Docker: OK
- Compose config: OK
- Traefik: OK
- Authelia: OK
- Nginx: OK
- PostgreSQL: OK
- UFW: OK
- WireGuard: OK
- Doctor: 100%

## Current Services

- Traefik
- Authelia
- Nginx public site
- Grafana
- Prometheus
- Loki
- Promtail
- cAdvisor
- Node Exporter
- Uptime Kuma
- Scrutiny
- Pi-hole
- PostgreSQL
- MariaDB
- Nextcloud
- Jellyfin

## Security Status

Validated:

- `.env` is not tracked
- `.env.bak` is not tracked
- `acme.json` is not tracked
- local vault wrapper does not contain credentials
- Git working tree clean after Phase 1 closure

Pending for higher maturity:

- automated secret scanning in CI
- image vulnerability scanning
- credential rotation policy
- hardened role-based operational model

## Documentation Status

The technical documentation baseline exists.

Executive documentation has been aligned for Phase 1 closure through:

- README
- PROJECT_STATUS
- ROADMAP
- SYSTEM_OVERVIEW
- PHASE_1_CLOSURE
- CHANGELOG
- SECURITY
- CONTRIBUTING
- LICENSE

## Next Milestone

Phase 2 begins with:

1. Storage inventory
2. NAS design
3. SMART disk audit
4. ZFS / TrueNAS decision
5. Backup and restore engine
6. Recovery runbooks
