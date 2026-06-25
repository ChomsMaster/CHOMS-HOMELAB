# Changelog

All notable changes to CHOMS-HOMELAB are documented here.

## v1.0.0-phase1 — Foundation Infrastructure Complete

### Added

- Debian 13 foundation
- Docker and Docker Compose stack
- Modular Docker Compose architecture
- Traefik reverse proxy
- HTTPS routing with Let's Encrypt
- Authelia authentication
- Public website routing
- Protected internal dashboards
- WireGuard VPN
- UFW firewall
- Fail2ban
- Pi-hole
- PostgreSQL
- MariaDB
- Nextcloud
- Jellyfin
- Grafana
- Prometheus
- Loki
- Promtail
- cAdvisor
- Node Exporter
- Uptime Kuma
- Scrutiny
- CHOMS CLI
- CHOMS Doctor
- CHOMS Health
- CHOMS Compose wrapper
- CHOMS Vault wrapper
- CHOMS service utilities
- Phase 1 documentation baseline

### Changed

- Moved from monolithic Compose structure to modular Compose files
- Refactored CHOMS CLI into modular command scripts
- Improved network checks for WireGuard and firewall status
- Documented Phase 1 closure

### Security

- Validated that `.env`, `.env.bak` and `acme.json` are not tracked
- Confirmed vault wrapper does not contain plaintext credentials
- Added security documentation baseline

### Status

Phase 1 closed.

Next: Phase 2 — Backups, resilience and recovery.
