# CHOMS-HOMELAB Services

## Public

| Service | Domain | Access |
|---|---|---|
| Website | www.chomsmaster.com | Public |
| Nextcloud | cloud.chomsmaster.com | Public + Nextcloud login |
| Jellyfin | jellyfin.chomsmaster.com | Public + Jellyfin login |

## Private

| Service | Domain | Access |
|---|---|---|
| Home Dashboard | home.chomsmaster.com | Authelia |
| Grafana | grafana.chomsmaster.com | Authelia |
| Uptime Kuma | kuma.chomsmaster.com | Authelia |
| Traefik Dashboard | traefik.chomsmaster.com | Authelia |
| Authelia | auth.chomsmaster.com | Public login endpoint |

## Internal

| Service | Access |
|---|---|
| PostgreSQL | localhost only |
| MariaDB | Docker network only |
| Prometheus raw port | Docker network only |
| Loki raw port | Docker network only |
| Node Exporter | Docker network only |
| cAdvisor | Docker network only |
