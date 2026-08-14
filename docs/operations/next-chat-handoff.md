# Next Chat Handoff

## Last Updated

2026-08-14

## Current Objective

Continue stabilizing and documenting the CHOMS Kubernetes platform without
rediscovering infrastructure that has already been validated.

## Infrastructure

| System | Address | Function |
|---|---|---|
| `node-dev-01` | `192.168.1.150` | Administration workstation |
| `choms-node-01` | `192.168.1.138` | K3s control plane |
| `choms-node-02` | `192.168.1.172` | K3s worker |
| `choms-node-03` | `192.168.1.134` | K3s worker |
| `choms-nas` | `192.168.1.167` | NFS storage |
| MetalLB VIP | `192.168.1.240` | Traefik edge address |

All three Kubernetes nodes run Debian 13 and are Ready.

## Validated Platform State

- No unhealthy Pods were detected.
- All persistent volume claims were Bound.
- The Traefik Gateway was programmed at `192.168.1.240`.
- Runtime audit covered 35 workloads with zero uncovered workloads.
- Core applications and databases are versioned as Kubernetes manifests.
- Directly managed application images are pinned by digest.
- MetalLB `v0.15.2` is vendored as a native installation.
- Six Helm releases use locked chart versions and versioned values.
- The complete Helm server-side plan passed.
- Helm release state remained unchanged during planning.
- Kubernetes Secret values remain outside Git.

## Recent Commits

- `67f9797` — locked Helm release installer.
- `6e2d009` — vendored MetalLB native installation.
- `fd08b74` — versioned core applications and databases.
- `89ca54b` — versioned Threadfin Kubernetes integration.
- `11730fd` — Kubernetes secrets bootstrap.

## Media State

Threadfin exposes an HDHomeRun-compatible lineup to Jellyfin.

The last validated Threadfin lineup contained 356 channels.

Jellyfin previously showed stale entries from two removed large M3U tuners.
Wait for the guide refresh to finish before diagnosing the final channel
count.

## Current Uncommitted Documentation

The following canonical documents are being updated for the Kubernetes model:

- `PROJECT_STATUS.md`
- `SESSION_STATE.md`
- `SYSTEM_OVERVIEW.md`
- `docs/operations/BOOTSTRAP.md`
- `docs/operations/DEPLOY.md`
- `docs/operations/next-chat-handoff.md`

Review these files together before committing.

## Next Actions

1. Review the six-document diff and check for obsolete Docker-era statements.
2. Commit and push the canonical operational documentation update.
3. Update README, ROADMAP and master context in a separate change.
4. Validate backup and recovery for NFS-backed PVCs.
5. Add probes and resource controls to MariaDB and Redis.
6. Verify the final Jellyfin Live TV channel count.
7. Add declarative drift detection.

## Safety Rules

- Preserve unrelated user changes.
- Never commit `stacks/kubernetes/secrets/secrets.env`.
- Validate manifests before applying them.
- Do not delete PVCs during routine deployment.
- Keep historical ADRs as records of previous architectural decisions.
