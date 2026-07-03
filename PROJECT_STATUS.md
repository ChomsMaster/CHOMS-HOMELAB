# CHOMS-HOMELAB Project Status

## Current Phase

**Phase 1: Foundation Infrastructure — Completed**  
**Phase 1.5: Multi-node / NAS Transition — In Progress**  
**Phase 2: Backups, Resilience and Recovery — Ready to start**

## Current State Summary

CHOMS-HOMELAB has moved from a single-node Docker host to a small multi-machine homelab:

- `choms-node-01` — main Docker/services node, LAN `192.168.1.138`.
- `choms-node-02` — second compute node, LAN `192.168.1.172`, rename in progress.
- `choms-nas` — Debian NAS, LAN `192.168.1.167`.
- D-Link DGS-1016D — central Gigabit switch.
- DIGI router — current gateway, dynamic public IP.

## Validated

- Debian 13 base systems.
- Docker stack on node-01.
- Traefik / HTTPS service architecture.
- Authelia present.
- Monitoring stack present.
- WireGuard present.
- UFW active.
- NFS from NAS to node-01.
- LAN tested with iperf3: 750-940 Mbps depending on host/direction, 0 retransmissions.
- Switch/router backbone considered healthy.

## Storage Status

NAS storage is operational but temporary:

- `/srv/media` on RAID0, exported by NFS.
- `/srv/storage` on RAID0.
- No redundancy yet.
- Disk trust level: low / transitional.

Node-01 storage:

- `/data` for Docker/project state.
- `/media/ssd-media` for local media SSD.
- `/mnt/choms-media` for NAS media via NFS.

## Current Risks

- NAS arrays are RAID0; any disk failure loses that array.
- Public IP is dynamic; DDNS automation still pending.
- TV/Jellyfin issue not fully closed; probable TV cable/app/DLNA issue.
- Documentation in GitHub is behind the real infrastructure state.
- Some files in repo are one-line/minified and need formatting cleanup.
- Backup strategy not yet implemented.

## Immediate Priorities

1. Update repository documentation with current multi-node/NAS state.
2. Rename second node to `choms-node-02`.
3. Confirm Jellyfin media paths with NAS and local SSD.
4. Identify and configure external DLNA service if used.
5. Replace or test TV Ethernet cable.
6. Begin Phase 2 backups and resilience.
7. Implement DDNS/public IP automation.
8. Create recovery/runbook documentation.
