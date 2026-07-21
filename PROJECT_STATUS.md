# CHOMS Platform — Project Status

**Release line:** v2.0  
**Architecture:** Node 01 + Node 02 + NAS  
**Repository role:** canonical source of truth

## Operational baseline

| Component | State | Responsibility |
|---|---|---|
| `choms-node-01` | Operational | Edge, control, authentication, observability and application services |
| `choms-node-02` | Operational | PostgreSQL, Redis and Jellyfin |
| NAS | Operational | NFS-backed persistent data, media and backup targets |
| WireGuard | Operational | Secure remote connectivity; configuration intentionally unchanged |
| CHOMS Controller | Operational | Platform control API; implementation intentionally unchanged |

## Completed

- Multi-node service placement established.
- PostgreSQL, Redis and Jellyfin assigned to Node 02.
- Traefik, Authelia, monitoring and control workloads assigned to Node 01.
- NAS integrated through NFS.
- SSH hardened with key-only access, disabled root login and Fail2ban.
- Samba removed from the active platform.
- Repository synchronized and adopted as the source of truth.
- v1 material separated from current v2 documentation.
- Runtime data, credentials and generated artifacts excluded from the repository package.

## Active engineering priorities

1. Validate every Compose stack against its assigned node.
2. Complete tested backup and restore procedures for databases and application data.
3. Add automated repository checks for links, shell syntax, Python syntax and accidental secrets.
4. Standardize deployment through the CHOMS CLI and stack deployment scripts.
5. Record service recovery objectives and ownership in the inventory.

## Constraints

- Do not modify the production WireGuard configuration as part of repository cleanup.
- Do not modify CHOMS Controller behavior during the v2 documentation refactor.
- Do not commit `.env` files, certificates, databases, tokens, passwords or runtime datasets.

## Acceptance criteria for v2.0

- Current architecture is documented consistently across root and architecture documents.
- Node placement is unambiguous.
- No active documentation instructs operators to deploy Samba.
- Repository validation passes without tracked runtime secrets.
- Backup and recovery runbooks are executable and tested.
