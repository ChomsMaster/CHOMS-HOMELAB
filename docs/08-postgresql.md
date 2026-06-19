# PostgreSQL

## Overview

PostgreSQL is the primary relational database engine used within the CHOMS-HOMELAB platform.

The database service provides a robust and production-proven environment for backend development, API testing and future self-hosted applications.

Deploying PostgreSQL as part of the homelab allows experimentation with database administration while maintaining complete control over the environment.

---

# Why PostgreSQL?

Several database engines were considered before selecting PostgreSQL.

The main reasons include:

* Reliability
* SQL standard compliance
* Excellent performance
* Strong community support
* Native Docker support
* Ideal for backend development with Python and FastAPI

The database will become a core component of future CHOMS Master infrastructure services.

---

# Deployment

PostgreSQL runs inside a dedicated Docker container.

Persistent data is stored outside the container, ensuring database information survives container upgrades or recreation.

Current deployment includes:

* PostgreSQL 17
* Dedicated Docker network
* Persistent storage
* Local access only

---

# Security

Database access is intentionally restricted.

Current security measures include:

* No direct Internet exposure.
* Local access only.
* Docker isolation.
* Authentication enabled.
* Future VPN-only administration.

---

# Current Usage

The database currently serves as the primary SQL engine for infrastructure testing.

Future workloads include:

* FastAPI applications
* Backend services
* Internal business services
* Development environments

---

# Future Improvements

Planned enhancements include:

* Automated backups
* Database monitoring
* Replication experiments
* Performance tuning
* Multiple databases for independent services

