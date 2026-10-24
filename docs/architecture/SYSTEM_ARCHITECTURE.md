# CHOMS Platform

# System Architecture

**Version:** 1.0

**Status:** Living Document

**Owner:** Oscar Manuel Salcedo Chirinos

---

# 1. Purpose

This document defines the high-level architecture of CHOMS Platform.

It establishes the engineering principles, architectural layers, system boundaries and long-term direction of the platform.

Rather than describing implementation details, this document explains how every major component fits into the overall ecosystem.

Every future architectural document within this repository references this document as the primary source of architectural truth.

---

# 2. Vision

CHOMS Platform is a self-hosted engineering platform designed to provide enterprise-grade infrastructure using commodity hardware.

Its purpose extends beyond operating personal services.

The platform serves simultaneously as:

* A production infrastructure.
* An engineering laboratory.
* A software development platform.
* A learning environment.
* A portfolio demonstrating enterprise engineering practices.
* A foundation for future commercial and educational projects.

The architecture is intentionally designed to evolve continuously without requiring fundamental redesign.

---

# 3. Architectural Principles

The platform follows several fundamental engineering principles.

## Architecture before implementation

Every implementation begins with analysis, documentation and design.

Technology never drives architecture.

Architecture drives technology.

---

## Modularity

Every service should remain as independent as possible.

Each subsystem should be capable of evolving without affecting unrelated components.

---

## Scalability

Every phase must prepare the platform for future growth.

Infrastructure decisions should never prevent future expansion.

---

## Standardisation

Whenever practical, hardware, operating systems, deployment procedures and operational practices should be standardised.

Standardisation reduces complexity.

---

## Maintainability

Long-term maintenance always takes priority over short-term optimisation.

Solutions should remain understandable years after deployment.

---

## Documentation First

Every significant engineering decision must be documented.

Knowledge should never depend exclusively on memory.

---

## Automation

Any repetitive operational task should eventually become automated.

Manual processes are considered temporary solutions.

---

# 4. Architectural Layers

The platform is divided into independent architectural layers.

## Physical Infrastructure

Represents all physical hardware.

Examples include:

* Compute nodes.
* NAS.
* Networking equipment.
* Raspberry Pi.
* Storage devices.

---

## Operating Systems

Each physical device hosts a dedicated operating system appropriate for its role.

Examples include:

* Debian Linux.
* Future NAS operating system.
* Lightweight infrastructure services.

---

## Virtualisation and Containers

Services are deployed using containerised workloads whenever practical.

Future phases may introduce virtual machines and orchestration technologies.

---

## Platform Services

Shared infrastructure services include:

* Reverse proxy.
* Authentication.
* DNS.
* VPN.
* Monitoring.
* Logging.
* Databases.
* Object storage.
* Automation.

These services provide capabilities consumed by higher-level applications.

---

## Business Services

Applications built upon the platform.

Examples include:

* ChomsMaster.
* ShiftCore APIs.
* Educational platforms.
* Private cloud.
* Media services.
* AI services.
* Internal development tools.

---

# 5. Infrastructure Roles

Each node within the platform has a clearly defined responsibility.

Compute nodes execute workloads.

Storage nodes preserve information.

Infrastructure nodes provide shared services.

Networking devices transport traffic.

Monitoring systems observe platform health.

Authentication systems protect access.

This separation simplifies operations while improving scalability.

---

# 6. Core Components

The current architecture is built around several strategic components.

## Compute

Low-power enterprise mini computers.

Future standard:

Lenovo Tiny series.

---

## Storage

Dedicated NAS infrastructure.

Operating system isolated from user data.

Multiple HDD storage pools.

Future redundancy.

Future snapshots.

Future replication.

---

## Networking

Private LAN.

VPN connectivity.

Reverse proxy.

Internal DNS.

Secure remote administration.

---

## Security

Authentication.

Authorization.

Encrypted communication.

Certificate management.

Least-privilege access.

Continuous monitoring.

---

## Observability

Metrics.

Logs.

Dashboards.

Alerts.

Performance monitoring.

Capacity monitoring.

Historical analysis.

---

# 7. Scalability Strategy

Growth occurs incrementally through engineering phases.

Each phase introduces new capabilities without redesigning existing architecture.

Examples include:

Phase 1

Single-node infrastructure.

Phase 2

Dedicated NAS.

Multiple compute nodes.

Centralised storage.

Phase 3

Cluster preparation.

Shared services.

Infrastructure redundancy.

Future phases

High availability.

Container orchestration.

Distributed workloads.

Enterprise services.

---

# 8. Supported Projects

CHOMS Platform exists to support multiple independent initiatives.

Current and future projects include:

* CHOMS Master.
* ShiftCore.
* Educational infrastructure.
* VPN services.
* Personal cloud.
* Media streaming.
* Development environments.
* Artificial Intelligence workloads.
* Internal APIs.
* Research environments.

The architecture is intentionally designed so that every project shares common infrastructure while remaining logically independent.

---

# 9. Long-Term Direction

The platform is expected to evolve continuously over many years.

Future improvements include:

* Additional compute nodes.
* Enterprise networking.
* Kubernetes.
* Infrastructure as Code.
* High Availability.
* Disaster Recovery.
* Continuous Integration.
* Continuous Deployment.
* AI-assisted operations.
* Self-healing infrastructure.

The objective is not to predict every future requirement.

The objective is to build an architecture capable of adapting to future requirements.

---

# 10. Engineering Philosophy

CHOMS Platform is not built to demonstrate technologies.

It is built to demonstrate engineering.

Hardware will change.

Software will change.

Technologies will evolve.

Engineering principles should remain.

The success of the platform will therefore not be measured by the number of deployed services.

It will be measured by the quality, maintainability and longevity of the architecture supporting them.

---

# 11. Relationship with the Documentation

This document represents the highest architectural level of CHOMS Platform.

Lower-level documents provide implementation details for individual domains, including:

* Network Architecture
* Storage Architecture
* Compute Architecture
* Security Architecture
* Service Architecture
* Disaster Recovery
* High Availability
* Engineering Decision Records (ADR)

Together, these documents form the complete architectural reference for the platform.

---

# Final Statement

CHOMS Platform is not a server.

It is not a Homelab.

It is not a collection of Docker containers.

It is an engineering platform designed to evolve methodically through disciplined architecture, documentation and continuous improvement.

Every decision made within the project should reinforce that objective.
