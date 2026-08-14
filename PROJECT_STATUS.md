# CHOMS Platform Status

## Last Updated

2026-08-14

## Current Phase

Kubernetes platform stabilization and reproducibility.

## Current Infrastructure

| System | Address | Role |
|---|---|---|
| `node-dev-01` | `192.168.1.150` | Administration workstation |
| `choms-node-01` | `192.168.1.138` | K3s control plane |
| `choms-node-02` | `192.168.1.172` | K3s worker |
| `choms-node-03` | `192.168.1.134` | K3s worker |
| `choms-nas` | `192.168.1.167` | NFS storage |
| MetalLB VIP | `192.168.1.240` | Traefik edge address |

## Platform Edge

- Traefik uses Kubernetes Gateway API.
- MetalLB provides the stable LAN address `192.168.1.240`.
- cert-manager manages TLS certificates.
- Authelia provides ForwardAuth.
- CoreDNS provides split DNS for `chomsmaster.com`.

## Declarative Coverage

- Runtime workloads audited: 35.
- Runtime workloads without declarative ownership: 0.
- Direct Kubernetes manifests are versioned under `stacks/kubernetes`.
- Six Helm releases use locked chart versions.
- MetalLB `v0.15.2` is vendored as a native manifest.
- Directly managed images are pinned by digest.
- Secret values remain outside Git.

## Current Health

- Three nodes Ready.
- No unhealthy Pods.
- All PVCs Bound.
- Kubernetes Gateway programmed.
- Six Helm releases deployed.
- Helm plan validated without modifying release revisions.
- Branch `main` synchronized with `origin/main`.

## Current Priorities

1. Update canonical documentation.
2. Validate PVC and NAS backup recovery.
3. Improve MariaDB and Redis probes and resource controls.
4. Complete Jellyfin Live TV reconciliation.
5. Add declarative drift detection.
