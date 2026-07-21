# Storage Inventory

## NAS responsibilities

- NFS exports for application persistence.
- Media libraries consumed by Jellyfin and MiniDLNA.
- Backup targets for Node 01 and Node 02.

## Repository boundary

The repository contains configuration and automation only. It must not contain database files, application datasets, media, backup archives, TLS material or generated runtime state.

## Required controls

- Stable mount points and explicit mount dependencies.
- SMART and capacity monitoring.
- Backup retention and restore verification.
- Least-privilege NFS exports.
- Documented ownership for every dataset.
