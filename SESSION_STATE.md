# CHOMS-HOMELAB Session State

## Last Updated

2026-08-14

## Current Focus

Complete Kubernetes platform reproducibility, documentation and recovery
procedures after migration from the legacy Docker edge.

## Infrastructure

| System | Address | Function |
|---|---|---|
| `node-dev-01` | `192.168.1.150` | Ubuntu administration workstation |
| `choms-node-01` | `192.168.1.138` | K3s control plane |
| `choms-node-02` | `192.168.1.172` | K3s worker |
| `choms-node-03` | `192.168.1.134` | K3s worker |
| `choms-nas` | `192.168.1.167` | NFS storage |
| MetalLB VIP | `192.168.1.240` | Traefik LoadBalancer address |

All three Kubernetes nodes run Debian 13 and are Ready.

## Platform Services

The cluster currently runs:

- Home portal and public site
- CHOMS Controller
- Nextcloud, Portainer and Uptime Kuma
- PostgreSQL, MariaDB and Redis
- Jellyfin and Threadfin
- Filebrowser and qBittorrent
- Authelia and Traefik
- cert-manager and MetalLB
- Prometheus, Alertmanager and Grafana
- Loki and Alloy
- Scrutiny
- NFS external provisioner

## Declarative State

Completed reproducibility work:

- Core application and database manifests versioned.
- Threadfin Kubernetes integration versioned.
- MetalLB `v0.15.2` native installation vendored.
- Six Helm releases locked by chart version.
- Helm server-side plan validated successfully.
- Release revisions remained unchanged during planning.
- Runtime audit found zero uncovered workloads.
- Secret values remain excluded from Git.
- Directly managed application images are pinned by digest.

## Media State

Threadfin exposes an HDHomeRun-compatible lineup to Jellyfin.

Last validated Threadfin lineup size: 356 channels.

Jellyfin previously retained stale entries from two removed large M3U tuners.
The final channel count should be checked after its guide refresh finishes.

## Next Work

1. Update remaining canonical architecture and inventory documents.
2. Validate backup and recovery for NFS-backed PVCs.
3. Add probes and resource controls to MariaDB and Redis.
4. Verify Jellyfin Live TV reconciliation.
5. Introduce declarative drift detection.
