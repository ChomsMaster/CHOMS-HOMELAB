# Service Inventory

| Service | Node | Category | Exposure | State |
|---|---|---|---|---|
| Traefik | Node 01 | Edge | Public HTTPS entry point | Operational |
| Authelia | Node 01 | Identity | Internal/protected | Operational |
| WireGuard | Node 01 | Network | VPN endpoint | Operational |
| CHOMS Controller | Node 01 | Control plane | Restricted API | Operational |
| Prometheus / Grafana / Loki | Node 01 | Observability | Protected | Operational |
| Portainer / Uptime Kuma | Node 01 | Operations | Protected | Operational |
| Pi-hole | Node 01 | DNS | LAN/VPN | Operational |
| Nextcloud | Node 01 | Application | HTTPS with native login | Operational |
| Nginx public site | Node 01 | Application | Public HTTPS | Operational |
| MiniDLNA | Node 01 | Media discovery | LAN | Operational |
| Scrutiny | Node 01 | Storage monitoring | Protected | Operational |
| PostgreSQL | Node 02 | Database | Internal only | Operational |
| Redis | Node 02 | Cache/data | Internal only | Operational |
| Jellyfin | Node 02 | Media | HTTPS with native login | Operational |
