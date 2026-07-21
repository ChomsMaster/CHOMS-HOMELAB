# CHOMS-HOMELAB System Overview

CHOMS-HOMELAB v2 is a multi-node self-hosted platform built around explicit service placement and centralized operational governance.

## Topology

- **Node 01:** edge routing, authentication, VPN, CHOMS control services, observability and selected applications.
- **Node 02:** PostgreSQL, Redis and Jellyfin.
- **NAS:** NFS-backed persistent storage, media and backup targets.

The canonical visual topology and traffic flows are maintained in [`docs/architecture/PLATFORM_TOPOLOGY_V2.md`](docs/architecture/PLATFORM_TOPOLOGY_V2.md). Current service ownership is listed in [`docs/inventory/SERVICES.md`](docs/inventory/SERVICES.md).

## Operating model

Git is the source of truth for declarative configuration, scripts and documentation. Secrets, databases, certificates, logs and application data remain outside Git. Deployments are executed through the CHOMS operational tooling or the node-specific stack scripts and must be followed by health validation.

## Security model

The platform uses SSH key authentication, UFW, Fail2ban, Traefik HTTPS ingress, Authelia and WireGuard. The active WireGuard and CHOMS Controller implementations are operational dependencies and are not altered by the repository v2 refactor.
