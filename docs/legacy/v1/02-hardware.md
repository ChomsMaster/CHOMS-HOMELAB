# Hardware Platform

## Overview

The current infrastructure runs on an ACEPC AK2 Mini PC.

Rather than investing in enterprise hardware from the beginning, the decision was made to build the platform using affordable and readily available equipment. This approach allows every component of the infrastructure to be designed, tested and documented before considering future upgrades.

The hardware is intentionally modest, proving that a reliable self-hosted environment does not necessarily require expensive servers.

---

# Current Specifications

| Component             | Specification       |
| --------------------- | ------------------- |
| Platform              | ACEPC AK2           |
| Processor             | Intel Celeron J3455 |
| Memory                | 6 GB DDR3           |
| Operating System Disk | 128 GB SSD          |
| Data Disk             | 120 GB SSD          |
| Operating System      | Debian 13           |

---

# Storage Layout

The storage has been separated into two logical areas.

## System Disk

The primary SSD hosts:

* Debian Linux
* Docker
* WireGuard
* System configuration
* Installed packages

---

## Data Disk

A dedicated SSD stores persistent information such as:

* Docker volumes
* Database files
* Backups
* Future cloud storage
* Project data

Separating operating system files from application data simplifies maintenance, backup procedures and future migrations.

---

# Design Decisions

Several architectural decisions influenced the hardware selection.

* Low power consumption for continuous operation.
* Small physical footprint.
* Silent operation.
* Reuse of existing hardware.
* Easy future migration to more powerful systems.

The objective is to validate the complete infrastructure before investing in enterprise-grade hardware.

---

# Future Upgrades

Potential future improvements include:

* RAM expansion (hardware permitting).
* Larger SSD for application data.
* UPS integration.
* Hardware monitoring.
* Migration to higher-performance hardware while preserving the same architecture.

