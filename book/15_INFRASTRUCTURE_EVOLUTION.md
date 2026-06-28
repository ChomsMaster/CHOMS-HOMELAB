# Infrastructure Evolution

## Introduction

Infrastructure is rarely built correctly on the first attempt.

It evolves.

New requirements emerge.

Technologies mature.

Architectural understanding improves.

CHOMS Platform is no exception.

This document records the evolution of the infrastructure from its earliest concept to the long-term vision of becoming a complete engineering platform.

Rather than documenting only the final architecture, this chapter preserves the journey itself.

Understanding how the platform evolved is considered as valuable as understanding its current state.

---

# Stage 0 — Before CHOMS

Before any infrastructure existed, there was only an idea.

That idea was ShiftCore.

At the time, infrastructure was not considered part of the project.

The assumption was simple.

Applications would eventually be deployed somewhere.

Servers were merely considered an implementation detail.

That assumption would later change completely.

---

# Stage 1 — The VPN

The first real infrastructure component was not a server.

It was a VPN.

Living in Spain while maintaining strong connections with Venezuela created practical networking challenges.

Some online services were geographically restricted.

Secure communication between both countries became increasingly important.

The solution was to build private VPN infrastructure.

One endpoint would operate in Spain.

Another would eventually operate in Venezuela.

This became the first tangible engineering project.

Although relatively small, it introduced a fundamental concept.

Owning infrastructure provides freedom.

This was the true birth of CHOMS.

---

# Stage 2 — The Homelab

Another important event accelerated the project.

Commercial hosting was no longer financially sustainable.

Instead of renewing hosting services, a different approach was chosen.

Build everything.

Initially the objective was modest.

Host a personal website.

Maintain VPN services.

Run several Docker containers.

Nothing more.

At this stage the project became known as CHOMS-HOMELAB.

---

# Stage 3 — Engineering instead of experimentation

While researching Homelabs, an important realization appeared.

Many personal laboratories focused almost exclusively on deploying software.

Few documented engineering.

Even fewer documented architecture.

Very few documented decision making.

The project therefore changed direction.

Rather than creating another Homelab, the objective became creating a professional engineering platform.

Documentation became mandatory.

Architecture became mandatory.

Version control became mandatory.

Operational procedures became mandatory.

Engineering discipline became the distinguishing characteristic of the project.

---

# Stage 4 — Building the foundation

Phase One focused on creating a stable engineering baseline.

The objective was never quantity.

The objective was stability.

During this phase the platform incorporated:

Debian Linux.

Docker.

Docker Compose.

Traefik.

Authelia.

WireGuard.

Grafana.

Prometheus.

Loki.

Promtail.

Nextcloud.

Jellyfin.

Pi-hole.

PostgreSQL.

Monitoring.

Operational tooling.

Engineering documentation.

This became the foundation upon which every future phase would be built.

---

# Stage 5 — Infrastructure becomes a platform

As additional services were introduced, another conceptual change occurred.

Infrastructure itself was no longer the destination.

It became the foundation for something much larger.

The platform would eventually support:

ChomsMaster.

ShiftCore.

Educational systems.

Private cloud.

Artificial Intelligence.

Development environments.

Automation.

Future enterprise services.

The Homelab had evolved into an engineering platform.

---

# Stage 6 — The future NAS

As discussions around clustering and multiple compute nodes progressed, local storage quickly became insufficient.

The architecture required shared storage.

Initially, several alternatives were evaluated.

Local storage.

Commercial NAS appliances.

Self-built storage server.

During the hardware inventory, an unused desktop tower became available.

Rather than purchasing new hardware, the existing machine was selected as the future storage server.

The planned architecture includes:

A dedicated SSD for the operating system.

Five mechanical hard drives forming the storage pool.

Future snapshots.

Future replication.

Shared storage.

Backup repositories.

Persistent volumes.

Virtual machine storage.

This decision reflects one of the project's strongest engineering principles.

Reuse existing resources whenever they continue providing long-term value.

---

# Stage 7 — Standardising compute nodes

Future infrastructure expansion required another strategic decision.

Instead of acquiring random computers, the project began evaluating standard hardware.

Multiple platforms were compared.

Older desktop systems.

Mini PCs.

Apple hardware.

Enterprise workstations.

Lenovo Tiny systems gradually emerged as the preferred compute platform.

Their advantages include:

Compact design.

Low energy consumption.

DDR4 support.

NVMe compatibility.

Excellent Linux support.

Strong availability on the second-hand market.

Reasonable acquisition cost.

This standardisation simplifies future maintenance while reducing operational complexity.

---

# Stage 8 — Dedicated infrastructure roles

Another important architectural evolution involved assigning clear responsibilities.

Rather than allowing every machine to perform every task, dedicated roles emerged.

Storage server.

Compute nodes.

Networking.

Monitoring.

Authentication.

Future virtualization.

Future orchestration.

Each subsystem became responsible for a specific engineering capability.

This significantly improved long-term scalability.

---

# Stage 9 — Towards clustering

Although not yet implemented, the next stage of the platform has already been defined.

The infrastructure will gradually evolve from a single-node deployment into a multi-node environment.

Initial plans include:

Dedicated NAS.

Primary compute node.

Secondary compute node.

Raspberry Pi for infrastructure services.

Managed networking.

Future Kubernetes.

Future virtualization.

Future high availability.

Future distributed workloads.

The objective is controlled evolution rather than rapid expansion.

---

# Stage 10 — Beyond infrastructure

The long-term vision extends well beyond hardware.

Eventually the platform should become capable of supporting:

Software engineering.

Platform engineering.

Infrastructure engineering.

Artificial Intelligence.

Automation.

Education.

Personal cloud.

Business services.

Research.

Innovation.

The infrastructure therefore becomes an enabler rather than an objective.

---

# Lessons learned

Several important lessons have already shaped the platform.

Professional engineering does not require expensive hardware.

Documentation creates long-term value.

Architecture reduces future complexity.

Planning prevents unnecessary rework.

Methodology is more important than technology.

Incremental growth produces better engineering outcomes.

Every important decision deserves documentation.

These lessons will continue influencing every future phase.

---

# Looking forward

The current infrastructure is only the beginning.

Future versions will almost certainly differ significantly.

New hardware will arrive.

New services will appear.

Some technologies will disappear.

Others will replace them.

The platform will continue evolving.

This document exists to ensure that its history evolves alongside it.

Every server tells part of the story.

Together they document the evolution of CHOMS Platform from a simple VPN into a long-term engineering ecosystem.
