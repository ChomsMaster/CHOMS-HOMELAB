# Next Chat Handoff

Use this summary to start the next CHOMS-HOMELAB chat quickly.

## Context

CHOMS now has:

- `choms-node-01` at `192.168.1.138`, main Docker/services host.
- `choms-node-02` at `192.168.1.172`, Lenovo M710Q, rename pending/ongoing.
- `choms-nas` at `192.168.1.167`, Debian NAS.
- D-Link DGS-1016D central switch.
- DIGI router with dynamic public IP.

## Validated

- LAN is healthy: iperf3 750-940 Mbps, 0 retransmissions.
- NFS NAS media mount works on node-01.
- NAS movies available at `/mnt/choms-media/Movies`.
- Local SSD media available at `/media/ssd-media`.
- UFW is active and working.
- Cisco 1921/K9 is not part of production; keep for lab.

## Current immediate tasks

1. Rename node-02 to `choms-node-02`.
2. Identify DLNA service:

```bash
systemctl list-units --type=service | grep -Ei 'dlna|minidlna|readymedia|gerbera'
dpkg -l | grep -Ei 'minidlna|readymedia|gerbera'
```

3. Add NAS media source to DLNA service if needed.
4. Replace TV Ethernet cable.
5. Confirm Jellyfin Movies library includes:

```text
/media/ssd-media/Movies
/mnt/choms-media/Movies
```

6. Close iperf3 diagnostic port if still open.
7. Start Phase 2 backup/resilience design.
