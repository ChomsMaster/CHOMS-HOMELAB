# Node Inventory

| Hostname | Platform role | Principal workloads | Storage dependency |
|---|---|---|---|
| `choms-node-01` | Edge, control and observability | Traefik, Authelia, WireGuard, CHOMS Controller, Grafana, Prometheus, Loki, Portainer, Pi-hole, Nextcloud, Uptime Kuma, Scrutiny, Nginx, MiniDLNA | NAS/NFS for persistent application data |
| `choms-node-02` | Data and media | PostgreSQL, Redis, Jellyfin | NAS/NFS for media and protected backup targets |
| NAS | Storage | NFS exports, media and backups | Local disk pool |

IP addresses, credentials and environment-specific secrets are deliberately not recorded in this public inventory.
