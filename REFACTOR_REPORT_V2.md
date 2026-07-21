# CHOMS-HOMELAB v2 Repository Refactor Report

## Scope

Repository-wide normalization against the deployed Node 01 + Node 02 + NAS architecture. Production WireGuard and CHOMS Controller behavior were explicitly left unchanged.

## Applied changes

- Rebuilt the README as a professional GitHub landing page while preserving visual badges, Mermaid diagrams, navigation, tables and project identity.
- Replaced single-node and future-NAS language with the deployed v2 topology.
- Rewrote `PROJECT_STATUS.md`, `ROADMAP.md` and `SYSTEM_OVERVIEW.md`.
- Established `docs/architecture/PLATFORM_TOPOLOGY_V2.md` as the canonical topology.
- Normalized node, service and storage inventories.
- Removed duplicate `docs/ops` and root `engineering` trees after retaining their canonical equivalents.
- Retained superseded v1 material under `docs/legacy/v1` and historical root documents under `docs/history/v1-root`.
- Removed tracked-package copies of `.env`, Authelia secrets/database, Traefik ACME state, backup Compose files, Python bytecode and generated archives.
- Preserved `.env.example` files for configuration discovery.
- Removed the duplicate `COMPUTE_NODES.m` typo.

## Deliberately unchanged

- CHOMS Controller application behavior.
- WireGuard production behavior and configuration.
- Active deployment scripts beyond repository cleanup.
- Runtime data on deployed nodes.

## Recommended review before merge

1. Compare the refactored tree with `release/v2.0`.
2. Verify environment-specific Compose interpolation on both nodes.
3. Confirm that removed secret files remain available only in secure runtime locations.
4. Run the repository validation workflow.
5. Commit in a dedicated refactor commit before tagging `v2.0.0`.
