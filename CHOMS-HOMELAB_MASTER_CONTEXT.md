# CHOMS-HOMELAB MASTER CONTEXT

## Owner

Oscar Salcedo — CHOMS Master Technology Services  
Repository: `https://github.com/ChomsMaster/CHOMS-HOMELAB`  
Primary domain: `chomsmaster.com`  
Working LAN subnet: `192.168.1.0/24`

## Working Style

The user prefers action-first technical guidance:

- Give exact commands and configuration.
- Assume the recommended path unless options are explicitly requested.
- Keep operational answers short while troubleshooting.
- Avoid long motivational commentary during live operations.
- Preserve context in this file before moving to a new chat.

## Current Project Purpose

CHOMS-HOMELAB is a production-inspired self-hosted infrastructure platform for:

- Personal cloud services.
- Media services.
- Monitoring and observability.
- DevOps and systems administration learning.
- Professional portfolio evidence.
- Future CHOMS Master / ShiftCore infrastructure.
- Future multi-node cluster or lightweight orchestration.

The goal is not simply running containers. The goal is to build, operate and document a reproducible, scalable and secure infrastructure.

## Current Physical Architecture

The project has evolved from a single-node homelab into a small multi-machine infrastructure.

### Confirmed host inventory

| Role | Hostname | LAN IP | Notes |
|---|---|---:|---|
| Compute node 1 | `choms-node-01` | `192.168.1.138` | Former `choms-homelab`; main Docker/services node. |
| Compute node 2 | `choms-node-02` planned | `192.168.1.172` | Lenovo M710Q currently still being renamed from `choms-core-02`. |
| NAS | `choms-nas` | `192.168.1.167` | Debian NAS with RAID0 arrays for temporary media/storage. |
| Router | DIGI router | `192.168.1.1` | Current gateway. Public IP is dynamic via PPPoE. |
| Switch | D-Link DGS-1016D | unmanaged | Central Gigabit switch. Validated by iperf3. |
| Lab router | Cisco 1921/K9 | offline | Kept aside for Cisco IOS lab; not needed in production now. |

### Current network topology

```text
Internet
   |
DIGI Router
   |
D-Link DGS-1016D Gigabit Switch
   |-- choms-node-01
   |-- choms-node-02
   |-- choms-nas
   |-- TV / clients
```

Important design point: internal traffic between NAS and nodes goes through the switch, not through the router. The router is only involved for Internet/WAN, DHCP/gateway and traffic leaving the LAN.

## Naming Convention Decision

Use function-based names, not hardware names:

```text
choms-nas
choms-node-01
choms-node-02
choms-node-03
choms-router
choms-switch-01
```

Avoid names such as `master`, `primary`, `main`, or hardware labels unless the device truly has a unique role. Compute nodes should be treated as equivalent wherever possible.

## Current Node-01 State

Current hostname has been changed in `/etc/hosts` to:

```text
127.0.1.1    choms-node-01
```

Old project path remains intentionally unchanged:

```text
/data/projects/choms-homelab
```

Do not rename this path yet because systemd services and scripts still reference it.

### Node-01 mounted storage

From current `lsblk` and `fstab` state:

| Device | Mount | Type | Label | Purpose |
|---|---|---|---|---|
| SSD ~120 GB | `/` | ext4 | - | Debian system disk. |
| SSD ~960 GB | `/data` | ext4 | DATA | Docker, persistent data, project files. |
| SSD ~224 GB | `/media/ssd-media` | exFAT | MEDIA | Local media SSD. |
| NFS from NAS | `/mnt/choms-media` | nfs4 | - | NAS media export `/srv/media`. |
| External/shared HDDs | `/media/choms`, `/media/mac-win` | ntfs3/exfat | - | Shared media/archive drives if connected. |
| mmcblk0p1 1.9 TB | not currently mounted | ext4 | BACKUPS | Needs review; intended archive/backups. |

Current important fstab line for the NAS media share:

```text
192.168.1.167:/srv/media  /mnt/choms-media  nfs  defaults,_netdev,nofail  0  0
```

Confirmed working path for NAS movies from node-01:

```text
/mnt/choms-media/Movies
```

Confirmed working path for local SSD media on node-01:

```text
/media/ssd-media
```

For Jellyfin, the Movies library can contain both local and NAS paths during transition:

```text
/media/ssd-media/Movies
/mnt/choms-media/Movies
```

Long-term architecture target: persistent media should live on the NAS; nodes should mainly execute services.

## Current NAS State

NAS is Debian-based and currently temporary/experimental but operational.

### NAS storage layout

| Device/Array | Size | FS | Mount | Notes |
|---|---:|---|---|---|
| System SSD Kingston | ~120 GB | ext4/vfat/swap | `/`, `/boot/efi` | NAS OS disk. |
| md0 | ~5.5 TB | ext4 | `/srv/storage` | RAID0 from 2×3 TB disks. Temporary/untrusted. |
| md1 | ~3.6 TB | ext4 | `/srv/media` | RAID0 from 2×2 TB disks. Temporary/untrusted. |

Important warning: NAS disks are not trusted long-term. Current RAID0 provides capacity only, not redundancy. Future plan is a proper NAS/backups design with better disks and/or a second backup NAS.

### Current NAS export

Confirmed NFS export:

```text
/srv/media  192.168.1.0/24(rw,sync,no_subtree_check,root_squash)
```

Confirmed from node-01:

```text
192.168.1.167:/srv/media on /mnt/choms-media type nfs4
```

Confirmed content:

```text
/mnt/choms-media/Movies
/mnt/choms-media/Series
/mnt/choms-media/Music
/mnt/choms-media/Photos
/mnt/choms-media/HomeVideos
```

## Current Edge / Services State

The public application edge has been migrated from Docker Traefik on Node-01 to Kubernetes.

Current ingress architecture:

- MetalLB provides the stable LAN VIP `192.168.1.240`.
- Traefik runs inside Kubernetes and owns public HTTP/HTTPS ingress.
- The Kubernetes `Gateway` named `traefik` exposes listeners `web` and `websecure`.
- HTTPRoutes attach application hostnames to both listeners.
- cert-manager manages the Let's Encrypt certificate `choms-platform`.
- TLS terminates at Traefik Kubernetes using Secret `choms-platform-tls`.
- Authelia runs inside Kubernetes and provides ForwardAuth protection for protected routes.
- The Traefik dashboard is exposed through Kubernetes and protected by Authelia.
- Legacy Docker container `choms-traefik` has been removed.
- Jellyfin and Authelia use internal Kubernetes `ClusterIP` Services; their previous NodePorts have been removed.

Current public ingress path:

    Internet
      -> router/NAT TCP 80 and 443
      -> 192.168.1.240 (MetalLB)
      -> Traefik Kubernetes
      -> Gateway API / IngressRoute
      -> Kubernetes Services

Public application ports should not be exposed directly unless deliberately required.

NodePorts should not be used for application ingress when the service is already reachable internally through Traefik and Kubernetes networking.

## Current Public DNS / WAN State

- ISP: DIGI Spain.
- Previously behind CG-NAT; current router shows public IPv4 via PPPoE, so CG-NAT appears resolved.
- Public IP is dynamic and can change after router reboot/reconnect.
- DNS is manually updated for now.
- DDNS automation remains pending.

Important operational point: use domain/DDNS instead of relying on a fixed public IP.

## WireGuard State

Node-01 has WireGuard interface `wg0` active with listening port `51820` and at least one peer (`10.10.10.2/32`).

Keep WireGuard as the preferred future remote administration path. Router WAN should forward only the necessary VPN port and 80/443 for Traefik when required.

## Firewall State

UFW is active on node-01. Confirmed behavior:

- SSH works.
- Jellyfin local/direct port is allowed.
- WireGuard UDP 51820 is allowed.
- iperf3 port 5201 was blocked until explicitly opened.

Decision: do not keep `5201/tcp` open permanently. Open only for diagnostics, then close:

```bash
sudo ufw allow 5201/tcp
# run tests
sudo ufw delete allow 5201/tcp
sudo ufw reload
```

## Network Validation Results

Network has been validated using ping, ethtool and iperf3.

### Link status

Node-01 physical interface negotiated:

```text
Speed: 1000Mb/s
Duplex: Full
Auto-negotiation: on
Link detected: yes
```

### Ping validation

Pings from NAS/node(s) to router were stable with 0% loss. Minor sub-ms to low-ms latency variation is acceptable.

### iperf3 validation

Observed results across the LAN:

| Test | Approx throughput | Retransmissions |
|---|---:|---:|
| node-01 -> node-02 | ~941 Mbps | 0 |
| node-02 -> node-01 | ~830 Mbps | 0 |
| node-01 -> NAS | ~884-885 Mbps | 0 |
| NAS -> node-01 | ~753 Mbps | 0 |
| NAS -> node-02 | ~813-814 Mbps | 0 |
| node-02 -> NAS | ~829-830 Mbps | 0 |

Interpretation:

- Router is not suspected.
- D-Link switch is not suspected globally.
- Cable/router/switch backbone is considered validated.
- Differences by direction are normal and can come from CPU, NIC, drivers, TCP offload, or NAS hardware.
- `Retr: 0` is the strongest sign that the LAN is healthy.

## Jellyfin / DLNA / TV State

Problem: TV was kicked from playback / showed connection issue.

Findings:

- Playback from computer does not stop.
- Jellyfin server logs did not show a server crash.
- Network tests do not indicate switch/router failure.
- TV direct to router appeared stable.
- TV back on switch also appeared stable after reconnect.
- A likely issue was found: RJ45 cable/connector at TV lacks the locking tab, so it may have micro-disconnections.

Current suspicion ranking:

1. TV cable/connector or port-specific issue.
2. TV app / DLNA behavior.
3. Jellyfin DLNA fragility.
4. Switch failure is low probability after iperf3 validation.

Recommendation:

- Replace TV Ethernet cable with one whose RJ45 locking tab is intact.
- Avoid Jellyfin DLNA if it keeps behaving badly.
- Prefer official Jellyfin app/client where possible.
- If using separate DLNA server, identify it (`minidlna` / ReadyMedia / Gerbera) and add `/mnt/choms-media/Movies` as a media source.

## USB / Removable Media Policy

Debian Server minimal does not auto-mount arbitrary USB drives unless configured in `/etc/fstab`, udev, or a desktop automounter.

Security decision:

- Do not auto-mount arbitrary USB devices.
- Only trusted disks with known UUIDs should auto-mount.
- No autorun behavior exists on Debian Server like Windows autorun.

If a trusted SSD is configured by UUID in `fstab`, it can mount automatically regardless of USB port.

## Cisco 1921/K9 Decision

Hardware identified:

- Cisco 1921/K9 ISR router.
- 2× Gigabit Ethernet ports.
- Cisco IOS capable.
- Expansion slots present.
- Installed HWIC module identified as `HWIC-1ADSL`, an old ADSL modem module.

Decision:

- Do not use it in current CHOMS production path.
- Keep it aside for Cisco IOS / routing / VPN / ACL / VLAN lab.
- The ADSL module is not useful for current CHOMS.

## Immediate Next Tasks Before Opening New Chat

1. Finish renaming `choms-core-02` to `choms-node-02`:
   - `hostnamectl set-hostname choms-node-02`
   - update `/etc/hosts`
   - reboot and verify.
2. Confirm Jellyfin library paths:
   - local SSD: `/media/ssd-media/...`
   - NAS NFS: `/mnt/choms-media/Movies`
3. Identify the non-Jellyfin DLNA server:
   - `systemctl list-units --type=service | grep -Ei 'dlna|minidlna|readymedia|gerbera'`
   - `dpkg -l | grep -Ei 'minidlna|readymedia|gerbera'`
4. Replace or test TV Ethernet cable with intact RJ45 locking tab.
5. Close any temporary diagnostic firewall ports:
   - ensure `5201/tcp` is not left open.
6. Review `/archive` / `mmcblk0p1 BACKUPS` mount state on node-01.
7. Begin NAS documentation update:
   - temporary RAID0 media/storage.
   - NFS export `/srv/media`.
   - current risk: no redundancy.
8. Start Phase 2 formally: backups/resilience and storage design.
9. DDNS automation for dynamic DIGI public IP.
10. Push updated documentation to GitHub.

## Resume Prompt For New Chat

Continue CHOMS-HOMELAB from this state:

We now have a multi-machine CHOMS homelab: `choms-node-01` at `192.168.1.138`, `choms-node-02` planned at `192.168.1.172`, and `choms-nas` at `192.168.1.167`, all connected through a D-Link DGS-1016D Gigabit switch behind a DIGI router. Node-01 runs the main Docker stack: Traefik, Authelia, Nextcloud, Jellyfin, Grafana, Prometheus, Loki, Uptime Kuma, Pi-hole, PostgreSQL, MariaDB, cAdvisor, Node Exporter and supporting services. The NAS runs Debian with temporary RAID0 arrays: `/srv/media` (~3.6 TB) and `/srv/storage` (~5.5 TB). NAS exports `/srv/media` over NFS to node-01 at `/mnt/choms-media`; confirmed working path for NAS movies is `/mnt/choms-media/Movies`. Node-01 also has local SSD media at `/media/ssd-media`. Network validation with ethtool/ping/iperf3 shows Gigabit, 0 retransmissions, and 750-940 Mbps depending on direction; router/switch are considered healthy. Jellyfin/TV issue likely relates to TV cable/app/DLNA, not backbone network. Cisco 1921/K9 is kept aside for lab, not production. Next work: rename node-02, update docs/GitHub, identify DLNA server, configure Jellyfin/NFS media sources, replace TV Ethernet cable, and begin Phase 2 backups/resilience.
