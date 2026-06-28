# CHOMS Platform

# Storage Architecture

**Version:** 1.0

**Status:** Living Document

**Owner:** Oscar Manuel Salcedo Chirinos

---

# 1. Purpose

This document defines the storage architecture of CHOMS Platform.

Storage is considered one of the most critical components of the platform because every service ultimately depends on reliable, secure and scalable data management.

Unlike compute resources, which can be replaced relatively easily, data represents the most valuable asset of the platform.

The storage architecture is therefore designed to maximise integrity, availability, scalability and long-term maintainability.

---

# 2. Objectives

The storage architecture has been designed around the following objectives.

* Centralise all persistent data.
* Separate storage from compute workloads.
* Simplify backup operations.
* Enable future redundancy.
* Support future clustering.
* Protect business-critical information.
* Reduce hardware dependency.
* Support gradual expansion.

---

# 3. Design Philosophy

Storage is treated as a dedicated infrastructure service.

Application servers should never become permanent storage servers.

Instead, compute nodes consume storage services provided by a specialised storage platform.

This separation improves flexibility, simplifies maintenance and prepares the infrastructure for future distributed environments.

The architecture is designed around the principle that applications may move between compute nodes while their data remains permanently available.

---

# 4. Storage Node

The storage platform is built around a dedicated NAS server.

Rather than purchasing a commercial appliance, an existing desktop computer was intentionally selected and repurposed.

This decision reflects one of the core engineering principles of CHOMS Platform:

Reuse existing resources whenever they continue providing long-term value.

The NAS becomes a strategic component responsible for preserving every important dataset within the platform.

---

# 5. Hardware Architecture

The planned NAS hardware consists of:

Dedicated desktop tower.

Intel Core i5 processor.

Dedicated SSD exclusively for the operating system.

Five mechanical hard drives dedicated to persistent storage.

Multiple SATA interfaces allowing future expansion.

Gigabit Ethernet connectivity.

The operating system remains completely isolated from user data.

This separation simplifies maintenance while reducing operational risk.

---

# 6. Storage Responsibilities

The NAS is responsible for storing:

Application data.

Docker volumes.

Databases.

Media libraries.

Private cloud files.

Engineering documentation.

Source code backups.

Configuration backups.

Virtual machine images.

Container snapshots.

Future Kubernetes persistent volumes.

The NAS intentionally avoids executing production application workloads.

Its primary responsibility is preserving information.

---

# 7. Logical Storage Layout

The storage architecture follows a logical separation of data.

Example structure:

```text
/storage

├── backups
├── databases
├── docker
├── documents
├── engineering
├── media
│   ├── movies
│   ├── tv
│   ├── music
│   └── photos
├── nextcloud
├── repositories
├── snapshots
└── virtual-machines
```

Each directory represents an independent storage domain.

Future storage policies may differ for each domain.

---

# 8. Media Storage

The platform includes a dedicated multimedia library.

Media assets include:

Movies.

TV series.

Music.

Home videos.

Personal archives.

Original ISO images.

Whenever possible, optical media should be preserved as archival ISO images while Jellyfin consumes MKV versions extracted without quality loss.

This preserves the original media while providing maximum playback compatibility.

---

# 9. Data Protection

Data protection is considered mandatory.

Future implementations will progressively introduce:

Snapshots.

Versioned backups.

Scheduled backups.

Replication.

Integrity verification.

Recovery testing.

Off-site backup strategies.

The objective is to minimise data loss under every realistic failure scenario.

---

# 10. Future Redundancy

The storage architecture is intentionally designed to evolve.

Future phases may include:

RAID or equivalent storage redundancy.

ZFS evaluation.

Distributed storage.

NAS replication.

Remote backup servers.

Geographically separated backup locations.

Redundancy should protect against hardware failures while preserving operational simplicity.

---

# 11. Capacity Planning

Storage growth is expected throughout the lifetime of the platform.

Capacity planning follows several principles.

Expand incrementally.

Reuse hardware whenever practical.

Avoid unnecessary purchases.

Monitor utilisation continuously.

Maintain sufficient free capacity for future services.

Hardware expansion should never require redesigning the storage architecture.

---

# 12. Relationship with Other Services

The storage platform provides persistent storage for multiple services.

Examples include:

Nextcloud.

Jellyfin.

PostgreSQL.

Docker volumes.

Git repositories.

Engineering documentation.

Future Kubernetes workloads.

Every service consuming persistent information depends directly upon this architecture.

---

# 13. Long-Term Vision

The storage platform is expected to evolve into an enterprise-style storage service supporting every major component of CHOMS Platform.

Future capabilities include:

High-capacity storage pools.

Automated snapshots.

Replication.

Cloud synchronisation.

Disaster recovery.

Object storage.

Shared storage for clustered workloads.

Long-term archival.

The storage platform becomes one of the foundational pillars of the entire ecosystem.

---

# Engineering Decisions

Several engineering decisions have already been established.

Persistent storage must remain independent from compute nodes.

Existing hardware should be reused whenever practical.

Operating systems must remain isolated from user data.

Storage growth should occur incrementally.

Every storage decision must prioritise maintainability over short-term optimisation.

---

# Final Statement

Within CHOMS Platform, storage is not simply disk space.

It is the foundation upon which every application, every service and every engineering effort depends.

Protecting data is therefore equivalent to protecting the platform itself.

Every future storage decision should reinforce reliability, maintainability and long-term sustainability.
