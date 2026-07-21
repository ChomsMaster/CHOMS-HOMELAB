# CHOMS Platform Roadmap

The roadmap is organized by operational risk and platform value rather than by arbitrary feature count.

## v2.0 — Architecture normalization

**Status: in progress**

- Establish Node 01, Node 02 and NAS as the canonical topology.
- Consolidate documentation and archive the v1 single-node material.
- Normalize service and storage inventories.
- Remove runtime data, secrets and generated artifacts from distributable repository packages.
- Validate deployment entry points and repository checks.

## v2.1 — Backup and recovery

- Automate PostgreSQL backups with retention and integrity verification.
- Define Redis persistence and recovery policy.
- Back up Nextcloud configuration, database and NFS application data.
- Document Jellyfin rebuild and media-library recovery.
- Run and record a full restore exercise.
- Add `choms backup` and `choms restore` workflows.

## v2.2 — Deployment reliability

- Add preflight validation for node identity, mounts, ports and required environment variables.
- Make stack deployment idempotent.
- Add post-deployment health checks and rollback guidance.
- Introduce CI checks for Compose configuration, shell syntax, Python compilation, links and secret leakage.
- Publish versioned release notes and migration instructions.

## v2.3 — Observability and operations

- Define service-level indicators for critical services.
- Add alert routing and escalation rules.
- Standardize dashboards across both nodes and the NAS.
- Add capacity thresholds for CPU, memory, storage and database growth.
- Complete incident, maintenance and patch-management procedures.

## v2.4 — Controlled service expansion

Candidate services are admitted only after ownership, storage, backup, monitoring and recovery requirements are defined.

- Vaultwarden
- Gitea or Forgejo
- n8n
- Immich
- Filebrowser

## v3.0 — Orchestration evaluation

- Evaluate a third compute node based on measured capacity requirements.
- Compare Docker Compose management, Nomad and K3s against CHOMS operational constraints.
- Define service scheduling, secrets management and highly available ingress requirements.
- Preserve a reversible migration path from the v2 Compose platform.

## Non-goals

- Replacing stable infrastructure solely to adopt fashionable tooling.
- Introducing clustering before backup and recovery are proven.
- Storing secrets or runtime datasets in Git.
- Reintroducing Samba without an approved architecture decision record.
