# CHOMS-HOMELAB System Overview

## Purpose

CHOMS-HOMELAB is a production-inspired self-hosted infrastructure platform.

It is secure, observable, version controlled, reproducible and multi-node.

## Kubernetes Cluster

| Node | Address | Role |
|---|---|---|
| `choms-node-01` | `192.168.1.138` | K3s control plane |
| `choms-node-02` | `192.168.1.172` | K3s worker |
| `choms-node-03` | `192.168.1.134` | K3s worker |

K3s provides orchestration and containerd provides the container runtime.

## Traffic Flow

Client traffic reaches the MetalLB VIP `192.168.1.240`.
Traefik processes Kubernetes Gateway API routes and forwards requests to
internal ClusterIP Services. Authelia protects selected routes through
ForwardAuth.

## Networking

- LAN subnet: `192.168.1.0/24`
- Stable edge address: `192.168.1.240`
- Load balancer: MetalLB
- Routing: Traefik with Kubernetes Gateway API
- TLS: cert-manager with Let's Encrypt
- Authentication: Authelia ForwardAuth
- Internal resolution: CoreDNS split DNS
- Application Services normally remain `ClusterIP`

Application ingress should not use NodePort when the service is reachable
through Traefik and Kubernetes networking.

## Storage

The NAS at `192.168.1.167` exports NFS storage.

The `choms-nfs` StorageClass dynamically provisions persistent volumes with
a `Retain` reclaim policy. Stateful services use NFS-backed PVCs.

## Workload Management

CHOMS uses two declarative deployment models:

1. Direct Kubernetes manifests under `stacks/kubernetes`.
2. Locked Helm releases managed by
   `stacks/kubernetes/helm/apply-releases.sh`.

MetalLB uses a vendored upstream native manifest instead of Helm.
Directly managed images are pinned by digest and Helm versions are locked.

## Secret Management

Secret values are not stored in Git. The repository contains only Secret
references, an ignored local environment file, a safe example and the
versioned bootstrap script.

## Observability

- Prometheus collects metrics.
- Alertmanager handles alerts.
- Grafana provides dashboards.
- Loki stores logs.
- Alloy collects logs.
- Scrutiny monitors storage health.

## Source of Truth

Git is the desired-state source of truth. Runtime exports are used only for
auditing or controlled reconstruction and must be cleaned before versioning.
