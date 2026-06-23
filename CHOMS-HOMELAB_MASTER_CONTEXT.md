# CHOMS-HOMELAB MASTER CONTEXT

## Owner
Oscar Salcedo — CHOMS Master Technology Services  
GitHub: https://github.com/ChomsMaster/CHOMS-HOMELAB  
Domain: chomsmaster.com  
Main server LAN IP: 192.168.1.138  
Public IP configured in DNS: 79.112.15.233  
OS: Debian 13 Trixie  
Platform: ACEPC AK2 Mini PC  
CPU: Intel Celeron J3455  
RAM: 6 GB DDR3  
System SSD: 128 GB  
Main data SSD: 960 GB mounted under /data  
Media SSD: 240 GB mounted as /media/ssd-media  
Additional external storage: 1 TB shared HDD and 2 TB backup HDD

## Working Style
User prefers action-first technical guidance:
- Minimal motivational commentary.
- Give exact commands/configuration.
- Assume recommended path unless asked for options.
- Use “estado” only when user asks for broader status.
- Keep responses short during operations.

## Project Purpose
CHOMS-HOMELAB is a production-inspired self-hosted infrastructure platform for:
- Personal cloud services.
- Media services.
- Monitoring and observability.
- DevOps learning.
- Professional portfolio.
- Future CHOMS Master / ShiftCore infrastructure.
- Future multi-node cluster.

The objective is not just running containers, but building a reproducible, documented, scalable infrastructure.

## Current Architecture
Single-node Docker Compose infrastructure.

Main entrypoint:
- Traefik reverse proxy
- HTTP -> HTTPS redirection
- Let's Encrypt automatic certificates
- DNS managed in Namecheap
- Router forwards WAN 80/443 to 192.168.1.138

Public HTTPS services currently working:
- https://cloud.chomsmaster.com -> Nextcloud
- https://grafana.chomsmaster.com -> Grafana
- https://kuma.chomsmaster.com -> Uptime Kuma
- https://jellyfin.chomsmaster.com -> Jellyfin

DNS A records configured:
- @ -> 79.112.15.233
- cloud -> 79.112.15.233
- grafana -> 79.112.15.233
- jellyfin -> 79.112.15.233
- kuma -> 79.112.15.233
- traefik -> 79.112.15.233

## Current Services
Core:
- Docker
- Docker Compose
- Traefik
- Nginx
- PostgreSQL 17
- MariaDB for Nextcloud
- Pi-hole
- WireGuard planned/existing context but not current focus
- Fail2ban
- UFW

Applications:
- Nextcloud
- Jellyfin
- Uptime Kuma
- Grafana
- Prometheus
- Node Exporter
- cAdvisor
- Loki
- Promtail
- Scrutiny

Current important ports:
- 80/443 public via Traefik
- 8096 Jellyfin direct/local
- 3000 Grafana direct/local
- 3001 Kuma direct/local
- 8081 Pi-hole
- 8082 cAdvisor
- 8083 Scrutiny
- 9090 Prometheus
- 9100 Node Exporter
- 3100 Loki
- PostgreSQL bound to 127.0.0.1:5432

## Docker Layout
Main compose:
- /data/projects/choms-homelab/docker/compose.yml

Traefik dynamic config:
- /data/projects/choms-homelab/docker/traefik/config/dynamic.yml

Important persistent paths:
- /data/docker/monitoring/grafana
- /data/docker/monitoring/prometheus
- /data/docker/monitoring/uptime-kuma
- /data/docker/loki
- /data/docker/promtail
- /data/docker/scrutiny
- /data/docker/jellyfin/config
- /data/docker/jellyfin/cache
- /data/projects/choms-homelab/docker/nextcloud/html
- /data/projects/choms-homelab/docker/nextcloud/db
- /data/postgres
- /data/pihole

Secrets:
- docker/.env is private and must never be committed.
- .gitignore includes docker/.env and secrets patterns.
- Future plan: root-only vault under /root/choms/secrets.env and command sudo choms-secrets.

## Confirmed Technical State
Traefik:
- HTTPS working.
- Let's Encrypt certificates confirmed valid.
- cloud.chomsmaster.com works.
- grafana.chomsmaster.com works.
- kuma.chomsmaster.com works.
- jellyfin.chomsmaster.com returns HTTP/2 302 to /web/, expected Jellyfin behavior.

Nextcloud:
- Works behind Traefik.
- Config was updated from cloud.choms.local to cloud.chomsmaster.com:
  - overwrite.cli.url=https://cloud.chomsmaster.com
  - overwritehost=cloud.chomsmaster.com
  - overwriteprotocol=https
  - trusted_domains includes cloud.chomsmaster.com

Jellyfin:
- Works locally and via https://jellyfin.chomsmaster.com/web/
- Uses network_mode: host.
- Traefik routes Jellyfin through dynamic.yml using host.docker.internal:8096.
- DLNA caused heavy transcoding.
- Jellyfin CPU reached 365% during DLNA playback.
- Direct Play or better Jellyfin client is recommended.
- Use https://jellyfin.chomsmaster.com as server URL in clients.

Monitoring:
- Prometheus targets confirmed up:
  - cadvisor
  - node-exporter
  - prometheus
- Grafana works.
- Loki and Promtail work.
- Uptime Kuma works through HTTPS.
- Imported dashboards exist, but some old community dashboards may show N/A due label incompatibility.

## Current Design Decisions
- Use Traefik as single public ingress.
- Only WAN ports 80 and 443 should be public.
- Avoid exposing raw application ports publicly.
- Services should use subdomains.
- Secrets must stay outside Git.
- Keep architecture scalable toward future 2-4 node cluster.
- Do not split stateful apps across nodes until storage/HA is designed.
- Second node should initially be backup/monitoring/secondary workloads.
- Future 4-node vision:
  - Docker Swarm or Kubernetes
  - replicated storage: Longhorn/Ceph/ZFS replication
  - database HA: PostgreSQL Patroni or MariaDB Galera
  - redundant Traefik/load balancer
  - automated backups
  - service failover

## Immediate Next Tasks
1. Commit latest Jellyfin HTTPS changes.
2. Publish/protect Traefik dashboard or keep dashboard local-only.
3. Add Homepage dashboard at home.chomsmaster.com.
4. Add Authelia or equivalent access protection before exposing more admin services.
5. Harden security:
   - close public raw ports where possible
   - review UFW
   - ensure Fail2ban active
   - strong passwords
   - root-only secrets vault
6. Add backups:
   - Nextcloud files + DB
   - MariaDB
   - PostgreSQL
   - Docker configs
   - Jellyfin config
   - Pi-hole config
   - Traefik acme.json
7. Add DDNS automation for Namecheap/public IP changes.
8. Update README and docs to match current state.
9. Reorganize Traefik dynamic config into separate files before adding many more services.
10. Future services:
   - Homepage
   - Authelia
   - Vaultwarden
   - Gitea
   - Immich
   - n8n
   - Ollama/Open WebUI later if hardware allows

## Known Risks / Notes
- Raw public ports like 3000, 3001, 8081, 8082, 8083, 8096 may still be reachable if router forwards them or firewall allows them; public router currently forwards only 80/443, but local exposure remains.
- Do not expose Grafana/Kuma/Traefik publicly without strong passwords and ideally Authelia.
- Docker compose config shows resolved secrets from .env; this is normal, but do not paste those outputs publicly.
- Nextcloud and MariaDB are currently on same node; HA/storage replication not implemented.
- Jellyfin transcodes heavily via DLNA; use Direct Play clients.
- Some files in GitHub render minified/one-line because previous writes may have removed formatting; future cleanup recommended.

## Resume Prompt For New Chat
Continue CHOMS-HOMELAB from this state:
We have a Debian 13 single-node Docker Compose homelab at 192.168.1.138 with public IP 79.112.15.233 and domain chomsmaster.com. Traefik is the public HTTPS ingress with Let's Encrypt. Working public services: cloud.chomsmaster.com, grafana.chomsmaster.com, kuma.chomsmaster.com, jellyfin.chomsmaster.com. Nextcloud, Grafana, Uptime Kuma, Jellyfin, Prometheus, Node Exporter, cAdvisor, Loki, Promtail, Scrutiny, Pi-hole, PostgreSQL, MariaDB and Nginx are deployed. docker/.env contains private secrets and must not be committed. User wants action-first technical commands, minimal chatter, and scalable architecture toward future 4-node cluster. Next priority: commit current state, then add Homepage and Authelia, harden exposed services, implement backups, DDNS, and clean docs.
