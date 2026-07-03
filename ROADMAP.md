# CHOMS-HOMELAB Roadmap

## Phase 1 — Foundation Infrastructure

Status: **Completed**

Delivered:

- Debian 13 host.
- Docker and Docker Compose.
- Modular Docker stack.
- Traefik reverse proxy.
- Let's Encrypt / HTTPS routing.
- Authelia authentication.
- Nextcloud.
- Jellyfin.
- Monitoring stack: Grafana, Prometheus, Loki, Promtail, cAdvisor, Node Exporter, Uptime Kuma.
- Pi-hole.
- PostgreSQL / MariaDB.
- UFW and Fail2ban baseline.
- WireGuard baseline.
- CHOMS CLI / health tooling baseline.
- GitHub repository and documentation baseline.

## Phase 1.5 — Multi-node and NAS Transition

Status: **In Progress**

Delivered / validated:

- Added `choms-nas` Debian NAS.
- Added second compute node.
- Adopted node naming convention: `choms-node-01`, `choms-node-02`, etc.
- Centralized network through D-Link DGS-1016D switch.
- Validated Gigabit LAN with iperf3 and 0 retransmissions.
- NAS exports `/srv/media` via NFS.
- Node-01 mounts NAS media at `/mnt/choms-media`.
- Jellyfin can consume both node-local SSD media and NAS media.
- Cisco 1921/K9 evaluated and parked for lab use.

Remaining:

- Finish renaming node-02.
- Update all documentation and GitHub status.
- Confirm DLNA service and add NAS path if needed.
- Clean up node-01 `/archive` and backup disk mount state.
- Document NAS RAID0 risk.

## Phase 2 — Backups, Resilience and Recovery

Status: **Ready to start**

Planned:

- Define backup policy.
- Back up Docker configs and volumes.
- Back up Nextcloud files and MariaDB.
- Back up PostgreSQL.
- Back up Jellyfin config.
- Back up Pi-hole config.
- Back up Traefik `acme.json` and dynamic config.
- Create restore runbooks.
- Add backup verification.
- Decide long-term NAS disk strategy.
- Decide second NAS / offline backup strategy.

## Phase 3 — Service Expansion

Status: **Planned**

Candidates:

- Homepage dashboard.
- Vaultwarden.
- Gitea.
- n8n.
- Immich.
- Automation services.
- Additional operational dashboards.

## Phase 4 — Cluster Preparation

Status: **Planned**

Planned:

- Service placement strategy across nodes.
- K3s / Docker Swarm evaluation.
- Node inventory.
- Distributed monitoring.
- Shared storage design.
- Backup-aware scheduling.
- Possible HA ingress.
- Future 2.5/10 GbE upgrade for NAS if required.

## Phase 5 — Router / Network Lab

Status: **Optional / Lab**

- Cisco 1921/K9 for IOS learning.
- VLAN lab.
- ACL lab.
- Site-to-site VPN lab.
- Future OPNsense/pfSense evaluation.
