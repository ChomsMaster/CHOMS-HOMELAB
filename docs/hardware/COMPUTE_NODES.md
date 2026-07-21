# CHOMS Platform

# Compute Nodes

**Version:** 1.0

**Status:** Living Document

**Owner:** Oscar Manuel Salcedo Chirinos

---

# 1. Purpose

This document defines the compute infrastructure used throughout CHOMS Platform.

Compute nodes provide processing power for applications, containers, virtual machines and future orchestration platforms.

Each node should have a clearly defined operational role.

---

# 2. Philosophy

Compute resources should remain modular.

Rather than relying on a single powerful server, CHOMS Platform adopts a distributed architecture composed of multiple independent compute nodes.

This approach improves:

* Reliability.
* Scalability.
* Maintainability.
* Hardware replacement.
* Future clustering.

---

# 3. Node Classification

Compute nodes are classified according to their operational role.

## Infrastructure Nodes

Responsible for core platform services.

Examples:

* Reverse Proxy.
* Authentication.
* DNS.
* Monitoring.
* Logging.

---

## Application Nodes

Responsible for application workloads.

Examples:

* ShiftCore.
* APIs.
* Web Services.
* Databases.
* Internal tools.

---

## Laboratory Nodes

Dedicated to experimentation.

Examples:

* Virtual Machines.
* Kubernetes testing.
* New technologies.
* Hardware validation.

Laboratory nodes should remain isolated from production workloads whenever practical.

---

## AI Nodes

Reserved for future artificial intelligence workloads.

Examples:

* LLM inference.
* Machine Learning.
* Automation.
* AI-assisted services.

These nodes may require dedicated hardware accelerators in future phases.

---

# 4. Standard Specifications

Preferred minimum configuration.

CPU:

Intel Core i5 (6th Generation or newer)

Memory:

16 GB RAM minimum

Preferred:

32 GB

Storage:

256 GB SSD minimum

Networking:

Gigabit Ethernet minimum

Operating System:

Debian Stable

---

# 5. Compute Principles

Every node should:

Perform a clearly defined role.

Remain independently replaceable.

Be fully documented.

Support remote administration.

Integrate with monitoring.

Participate in backup policies.

Follow platform standards.

---

# 6. Virtualization

Virtualization should be used when it provides operational value.

Preferred technologies:

KVM

QEMU

libvirt

Cockpit Machines

Docker containers remain the preferred deployment model whenever virtual machines are unnecessary.

---

# 7. Resource Allocation

Compute resources should remain balanced.

Avoid:

One overloaded node.

Several underutilised nodes.

Resource allocation should evolve according to monitoring information.

---

# 8. Lifecycle

Every compute node follows:

Evaluation.

Procurement.

Deployment.

Monitoring.

Maintenance.

Upgrade.

Replacement.

Retirement.

---

# 9. Future Expansion

Future growth may include:

Additional Lenovo Tiny nodes.

Industrial fanless systems.

Dedicated AI hardware.

GPU-enabled compute.

High-speed networking.

Clustered infrastructure.

Infrastructure should remain prepared for gradual expansion.

---

# 10. Documentation

Every compute node should maintain an individual profile including:

Hardware specifications.

Serial number.

Assigned role.

Installed memory.

Storage configuration.

Operating system.

Network configuration.

Maintenance history.

Upgrade history.

Current operational status.

Each node becomes an engineering asset with its own lifecycle.

---

# Engineering Principles

Keep compute modular.

Scale horizontally whenever practical.

Avoid unnecessary hardware diversity.

Standardize deployments.

Document every node.

---

# Long-Term Vision

The compute layer will evolve from a small collection of individual systems into a distributed computing platform capable of supporting enterprise services, development environments, AI workloads and future orchestration technologies.

Each new compute node should strengthen the platform while preserving architectural consistency.

---

# Final Statement

Compute nodes are more than physical computers.

They are the execution layer of CHOMS Platform.

Their value is determined not by raw performance alone, but by how effectively they integrate into the overall engineering architecture.
