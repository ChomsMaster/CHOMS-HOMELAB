# CHOMS Platform

# Naming Conventions

**Version:** 1.0

**Status:** Living Document

**Owner:** Oscar Manuel Salcedo Chirinos

---

# 1. Purpose

This document defines the naming conventions used throughout CHOMS Platform.

Consistent naming improves readability, simplifies maintenance and reduces operational errors.

Every component within the platform should follow these conventions unless a documented exception exists.

---

# 2. General Principles

Names should be:

* Clear.
* Predictable.
* Consistent.
* Human readable.
* Technology independent whenever possible.

Names should describe purpose rather than implementation.

Avoid abbreviations unless they are universally recognised.

---

# 3. Project Names

Projects use Pascal Case.

Examples:

* CHOMS Platform
* ShiftCore
* CHOMS Master

Repository names use lowercase with hyphens.

Examples:

```text
choms-platform
shiftcore
chomsmaster-web
```

---

# 4. Server Names

Server names describe their primary responsibility.

Examples:

```text
choms-core

choms-storage

choms-compute-01

choms-compute-02

choms-monitoring

choms-backup

choms-ai
```

Avoid naming servers after hardware models.

Wrong:

```text
lenovo01

asus-mini

pc1
```

Hardware changes.

Responsibilities remain.

---

# 5. Docker Containers

Container names should describe services.

Examples:

```text
traefik

grafana

prometheus

postgres

nextcloud

jellyfin

authelia
```

Avoid unnecessary prefixes.

---

# 6. Docker Networks

Networks describe communication domains.

Examples:

```text
frontend

backend

monitoring

database

storage
```

Avoid generic names such as:

```text
network1

docker-net

bridge2
```

---

# 7. Docker Volumes

Volumes should indicate the data they contain.

Examples:

```text
postgres-data

grafana-data

nextcloud-data

jellyfin-media

prometheus-data
```

---

# 8. Directories

Directories use lowercase with hyphens.

Examples:

```text
docker/

scripts/

backups/

engineering/

architecture/

media/

movies/

tv/

music/
```

---

# 9. Documents

Documents use uppercase with underscores.

Examples:

```text
SYSTEM_ARCHITECTURE.md

NETWORK_ARCHITECTURE.md

PROJECT_CHARTER.md

ENGINEERING_HANDBOOK.md

VERSIONING_POLICY.md
```

The document title inside the file should remain human readable.

---

# 10. ADR Documents

ADR documents follow sequential numbering.

Examples:

```text
ADR-001-WHY_DEBIAN.md

ADR-002-WHY_DOCKER.md

ADR-003-STORAGE_STRATEGY.md
```

Numbers are never reused.

Deprecated ADRs remain in the repository.

---

# 11. Infrastructure Services

Whenever practical, service names should match their official product names.

Examples:

Traefik.

Grafana.

Prometheus.

Loki.

Authelia.

WireGuard.

PostgreSQL.

This simplifies onboarding.

---

# 12. Backups

Backup names follow a predictable structure.

Example:

```text
YYYY-MM-DD_service_backup.tar.gz
```

Examples:

```text
2026-06-27_postgres_backup.tar.gz

2026-06-27_nextcloud_backup.tar.gz
```

---

# 13. Scripts

Scripts use lowercase with hyphens.

Examples:

```text
install-jellyfin.sh

backup-postgres.sh

update-containers.sh

health-check.sh
```

Scripts should begin with a verb describing their primary action.

---

# 14. Git Branches

Recommended branch names.

```text
feature/

bugfix/

hotfix/

docs/

release/
```

Examples:

```text
feature/storage-server

feature/phase-2

docs/network-architecture

bugfix/jellyfin-permissions

release/v1.0
```

---

# 15. Version Numbers

Semantic Versioning should be used whenever practical.

```text
Major.Minor.Patch
```

Example:

```text
1.0.0

1.1.0

1.1.3

2.0.0
```

---

# 16. Future Scalability

Naming conventions should remain stable regardless of platform growth.

Whether the platform contains:

One server.

Ten servers.

One hundred services.

Multiple sites.

The naming strategy should remain unchanged.

---

# Engineering Principles

Good names reduce documentation.

Good names reduce mistakes.

Good names simplify operations.

Consistency is more valuable than personal preference.

Changing names unnecessarily creates technical debt.

---

# Final Statement

Naming is one of the simplest engineering decisions.

It is also one of the most important.

A predictable naming convention improves communication, reduces operational risk and ensures that CHOMS Platform remains understandable as it continues to evolve.
