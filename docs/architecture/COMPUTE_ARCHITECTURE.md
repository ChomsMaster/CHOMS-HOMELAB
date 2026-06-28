# CHOMS Platform

# Compute Architecture

**Version:** 1.0

**Status:** Living Document

**Owner:** Oscar Manuel Salcedo Chirinos

---

# 1. Purpose

This document defines the compute architecture of CHOMS Platform.

Its purpose is to establish how computational resources are organised, assigned and evolved throughout the different phases of the project.

Rather than treating every computer as an isolated machine, CHOMS Platform considers every node as part of a unified compute infrastructure.

---

# 2. Objectives

The compute architecture has been designed to achieve several long-term objectives.

* Low acquisition cost.
* Low power consumption.
* High maintainability.
* Incremental scalability.
* Hardware standardisation.
* Easy replacement of failed nodes.
* Support for enterprise workloads.
* Long operational life.

The architecture prioritises engineering quality over raw performance.

---

# 3. Design Philosophy

Compute capacity should never depend on a single powerful machine.

Instead, the platform grows by incorporating multiple specialised nodes.

This approach provides several advantages.

Lower operational risk.

Simpler maintenance.

Progressive expansion.

Hardware independence.

Future clustering capabilities.

The platform therefore follows a distributed mindset from its earliest stages.

---

# 4. Compute Roles

Each compute node is assigned a primary responsibility.

## Infrastructure Node

Responsible for hosting shared infrastructure services.

Examples include:

* Reverse Proxy
* Authentication
* Monitoring
* Logging
* DNS
* VPN
* Automation

Current implementation:

Intel Celeron J3455 Mini PC.

---

## Compute Nodes

Responsible for executing application workloads.

Examples include:

* Docker containers.
* APIs.
* Internal services.
* Development environments.
* AI workloads.
* Future Kubernetes workers.

Initial hardware target:

Lenovo Tiny Series.

---

## Storage Node

Dedicated exclusively to storage.

Responsibilities include:

Persistent volumes.

Media library.

Private cloud.

Backups.

Snapshots.

Replication.

Shared storage.

The storage node should avoid running unrelated application workloads.

---

## Auxiliary Nodes

Lightweight devices supporting specialised infrastructure.

Examples:

Raspberry Pi.

Future DNS.

VPN endpoint.

Infrastructure monitoring.

Automation.

Network services.

---

# 5. Current Infrastructure

The current platform consists of a single infrastructure node running Debian Linux.

This node currently hosts:

Docker.

Traefik.

Authelia.

Monitoring stack.

Networking services.

Infrastructure tooling.

As additional hardware becomes available, responsibilities will gradually migrate to dedicated nodes.

---

# 6. Hardware Standardisation

One of the strategic decisions of the project is to standardise compute hardware whenever possible.

After evaluating several alternatives, Lenovo Tiny systems were selected as the preferred compute platform.

Reasons include:

Compact form factor.

Excellent Linux compatibility.

DDR4 memory.

NVMe support.

Low electrical consumption.

Enterprise reliability.

Strong availability in the second-hand market.

Reasonable acquisition cost.

Standardisation significantly reduces maintenance complexity.

---

# 7. Scaling Strategy

Compute capacity increases horizontally.

Instead of replacing existing hardware, new nodes are incorporated into the platform.

Growth therefore becomes additive.

Node 1

Infrastructure.

Node 2

Application workloads.

Node 3

Additional services.

Node 4

AI or specialised processing.

Future nodes

Cluster expansion.

This approach maximises hardware reuse while reducing unnecessary expenditure.

---

# 8. Resource Allocation

Every compute node should reserve resources for future growth.

CPU utilisation should remain below sustained saturation.

Memory should include operational headroom.

Storage should remain independent from compute workloads.

Resource planning should always anticipate future requirements.

---

# 9. Operational Principles

Compute nodes should remain interchangeable whenever practical.

Configuration management should minimise manual intervention.

Services should be reproducible.

Deployment should be automated.

Monitoring should be continuous.

Documentation should accompany every major infrastructure change.

---

# 10. Future Evolution

Future versions of the compute architecture are expected to introduce:

Multiple Lenovo Tiny compute nodes.

Dedicated Kubernetes workers.

Virtualisation hosts.

GPU-enabled AI nodes.

Infrastructure automation.

Cluster management.

High Availability.

Self-healing workloads.

Distributed scheduling.

The architecture intentionally supports these capabilities without requiring major redesign.

---

# 11. Relationship with Other Architectural Domains

The compute architecture depends on and interacts with:

Storage Architecture.

Network Architecture.

Security Architecture.

Observability Architecture.

Disaster Recovery.

High Availability.

Together these domains define the complete operational model of CHOMS Platform.

---

# Final Statement

The compute architecture is designed to evolve through small, carefully planned increments.

Rather than relying on increasingly powerful hardware, CHOMS Platform grows through disciplined engineering, hardware standardisation and distributed compute resources.

This philosophy ensures that every new node strengthens the platform while preserving architectural consistency.
