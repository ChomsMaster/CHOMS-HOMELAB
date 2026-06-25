# CHOMS-HOMELAB Roadmap

## Phase 1 — Foundation Infrastructure

Status: **Completed**  
Release tag: **v1.0.0-phase1**

### Delivered

- Debian 13 base system
- Docker runtime
- Docker Compose
- Modular Compose layout
- Traefik reverse proxy
- Let's Encrypt HTTPS
- Authelia authentication
- Public website
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
- CHOMS Vault wrapper
- CHOMS Compose wrapper
- Documentation baseline
- GitHub versioned release

## Phase 2 — Backups, Resilience and Recovery

Status: **Next**

### Goals

Transform CHOMS from "working infrastructure" into "recoverable infrastructure."

### Planned Work

- inventory all available disks
- SMART health audit
- classify disks by reliability
- design NAS role
- decide between TrueNAS SCALE and Debian + ZFS
- define storage pools
- define snapshot strategy
- define backup policy
- implement `choms backup`
- implement `choms restore`
- automate backup verification
- document disaster recovery process

### Acceptance Criteria

Phase 2 is complete when:

- backup jobs run successfully
- at least one restore test has been performed
- critical configs are recoverable
- database dumps are automated
- disk health is observable
- recovery runbook is documented

## Phase 3 — Service Expansion

Status: **Planned**

Candidate services:

- Vaultwarden
- Gitea
- n8n
- Immich
- MinIO
- BookStack / Wiki.js

Phase 3 should only start after backups and recovery are operational.

## Phase 4 — Network and Security Maturity

Status: **Planned**

Planned capabilities:

- OPNsense / pfSense firewall
- managed switch
- VLANs
- server network
- IoT network
- guest network
- lab network
- IDS / IPS evaluation
- improved alerting
- certificate and secrets policy

## Phase 5 — Cluster and Platform Engineering

Status: **Future**

Planned capabilities:

- additional mini PC nodes
- service placement model
- K3s evaluation
- CI/CD pipelines
- GitHub Actions
- automated deployment
- infrastructure validation
- distributed monitoring
- platform documentation

## Long-Term Vision

CHOMS-HOMELAB should evolve into a reproducible, documented and secure infrastructure platform that demonstrates real-world operations, automation and platform engineering practices.
