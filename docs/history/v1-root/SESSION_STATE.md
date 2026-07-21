# CHOMS-HOMELAB Session State

## Last Updated

2026-07-03

## Current Focus

The current chat became too long. The next chat should continue from the updated master context and focus on operational work, not rediscovering prior state.

## Current Infrastructure

- `choms-node-01` (`192.168.1.138`) — main services node, former `choms-homelab`.
- `choms-node-02` (`192.168.1.172`) — Lenovo M710Q node, rename pending/ongoing.
- `choms-nas` (`192.168.1.167`) — Debian NAS.
- Router: DIGI, gateway `192.168.1.1`, dynamic public IP via PPPoE.
- Switch: D-Link DGS-1016D Gigabit.
- Cisco 1921/K9: set aside for lab only.

## Current Services on Node-01

Running Docker stack includes:

- Traefik
- Authelia
- Nextcloud
- Jellyfin
- Grafana
- Prometheus
- Loki
- Promtail
- Uptime Kuma
- Pi-hole
- PostgreSQL
- MariaDB
- cAdvisor
- Node Exporter
- Nginx public site

## Network Validation

- Physical link on node-01 is 1000 Mbps Full Duplex.
- Ping tests to router stable with 0% loss.
- iperf3 tests between nodes/NAS show 750-940 Mbps depending on direction.
- Retransmissions observed: 0.
- Backbone switch/router/cables are considered healthy.

## NAS State

- `/srv/media` exported over NFS to `192.168.1.0/24`.
- Node-01 mounts it at `/mnt/choms-media`.
- Movies available at `/mnt/choms-media/Movies`.
- RAID0 arrays are temporary and not redundant.

## Media State

Jellyfin can use two sources in the Movies library:

```text
/media/ssd-media/Movies
/mnt/choms-media/Movies
```

TV issue likely caused by cable/TV/DLNA, not core LAN. RJ45 connector at TV lacks locking tab and should be replaced.

## Next Commands To Run

### Rename node-02

```bash
sudo hostnamectl set-hostname choms-node-02
sudo nano /etc/hosts
sudo reboot
hostname
hostnamectl
```

### Identify DLNA service

```bash
systemctl list-units --type=service | grep -Ei 'dlna|minidlna|readymedia|gerbera'
dpkg -l | grep -Ei 'minidlna|readymedia|gerbera'
```

### Verify NAS media mount on node-01

```bash
mount | grep choms-media
findmnt /mnt/choms-media
ls -lah /mnt/choms-media/Movies
```

### Ensure iperf port is closed after testing

```bash
sudo ufw status
sudo ufw delete allow 5201/tcp
sudo ufw reload
```
