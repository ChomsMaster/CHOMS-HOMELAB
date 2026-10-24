# CHOMS Platform

# Storage Nodes

**Version:** 1.0

**Status:** Living Document

**Owner:** Oscar Manuel Salcedo Chirinos

---

# 1. Purpose

This document defines the storage architecture adopted by CHOMS Platform.

Storage nodes are responsible for preserving persistent data, protecting engineering assets and providing reliable long-term storage services for the entire platform.

Storage is considered one of the most critical infrastructure components.

---

# 2. Philosophy

Storage should remain independent from compute.

Applications execute on compute nodes.

Data remains on storage nodes.

Separating these responsibilities simplifies maintenance, improves scalability and reduces recovery time following hardware failures.

---

# 3. Objectives

The storage platform aims to:

* Protect persistent data.
* Centralize storage management.
* Simplify backups.
* Support future expansion.
* Reduce operational risk.
* Enable reliable disaster recovery.

---

# 4. Storage Responsibilities

Storage nodes host:

* Docker persistent volumes.
* Databases.
* Engineering documentation.
* Git repositories.
* Nextcloud data.
* Media libraries.
* Backup archives.
* Virtual machine images (future).
* ISO repository.
* Configuration backups.

No production service should permanently store critical data on compute nodes.

---

# 5. Storage Architecture

The preferred storage architecture consists of:

Operating System

↓

Dedicated SSD

↓

Persistent Data

↓

Independent storage pool

↓

Backup destination

Operating system storage should remain isolated from user data whenever practical.

---

# 6. Storage Types

The platform may combine multiple storage technologies.

Examples:

SSD

Operating system.

Containers.

Cache.

Virtual machine storage.

---

HDD

Large data repositories.

Media.

Archives.

Backups.

Long-term storage.

---

Future Expansion

NVMe cache.

RAID.

ZFS.

Distributed storage.

Snapshot technologies.

---

# 7. Data Classification

Storage should distinguish between:

Critical Data

Databases.

Documentation.

Certificates.

Secrets.

Configuration.

Repositories.

---

Important Data

Media metadata.

Application settings.

Monitoring dashboards.

Virtual machine templates.

---

Recreatable Data

Caches.

Temporary files.

Container images.

Downloaded packages.

Log archives.

---

# 8. Storage Growth

Storage expansion should follow engineering planning.

Preferred order:

Increase available capacity.

Improve redundancy.

Improve performance.

Improve availability.

Storage upgrades should anticipate future demand rather than respond to shortages.

---

# 9. Reliability

Storage reliability includes:

SMART monitoring.

Filesystem health.

Backup verification.

Temperature monitoring.

Capacity monitoring.

Integrity validation.

Reliability should always take priority over maximum capacity.

---

# 10. Future Features

Planned storage capabilities include:

Snapshots.

Versioning.

Replication.

Immutable backups.

Off-site synchronization.

Storage encryption.

Future cloud integration.

---

# 11. Node Documentation

Every storage node should maintain:

Hardware specifications.

Drive inventory.

Filesystem configuration.

Mount points.

Storage pools.

Backup destinations.

Expansion history.

Operational status.

---

# 12. Relationship with Other Documents

This document complements:

Storage Architecture.

Backup Policy.

Disaster Recovery.

Capacity Management.

NAS Documentation.

Hardware Standardization.

---

# Engineering Principles

Protect data first.

Separate storage from compute.

Expand before exhaustion.

Monitor continuously.

Document every storage change.

---

# Long-Term Vision

Storage infrastructure will evolve from a single NAS into a scalable storage platform supporting multiple compute nodes, virtualization workloads, engineering repositories and future AI services.

Storage should remain the most reliable layer of CHOMS Platform.

---

# Final Statement

Hardware executes services.

Storage preserves value.

The reliability of CHOMS Platform ultimately depends on the integrity, availability and protection of the information stored within its storage infrastructure.
