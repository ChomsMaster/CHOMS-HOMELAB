# Engineering Memory

## Why this document exists

Most engineering projects document what was built.

Very few document how decisions evolved.

Even fewer explain why certain ideas were abandoned while others became part of the final architecture.

CHOMS Platform intentionally preserves its engineering memory.

This document records the evolution of important technical decisions throughout the lifetime of the project.

It is not an Architecture Decision Record (ADR).

It is the story behind those decisions.

The objective is simple.

Years from now, anyone reading this repository should understand not only what the platform became, but also how it got there.

---

# Engineering memory matters

Engineering is not a straight line.

Every mature architecture is the result of hundreds of conversations, evaluations, experiments and revisions.

Many of the best ideas were not the first ideas.

Some technologies were adopted.

Others were rejected.

Some decisions were reversed.

Others became permanent.

This document preserves that evolution.

Future contributors should never have to guess why the platform looks the way it does.

---

# Timeline of major decisions

## Decision 001

### ShiftCore was the original project

The original objective was not to build infrastructure.

The first vision focused on ShiftCore, a software platform intended to orchestrate workflows and automate repetitive business processes.

Infrastructure was initially considered something that would simply exist somewhere else.

Only later did the need for complete infrastructure ownership become obvious.

Status

Completed.

---

## Decision 002

### VPN infrastructure became the first implementation

Before CHOMS Platform existed, a practical problem appeared.

Living in Spain while maintaining personal and professional connections with Venezuela required secure access between both countries.

A VPN was deployed before the Homelab itself existed.

This became the real starting point of the infrastructure journey.

Status

Completed.

---

## Decision 003

### Losing commercial hosting changed the direction

The inability to continue paying for commercial hosting created an unexpected opportunity.

Instead of purchasing another hosting plan, the decision was made to build a personal infrastructure.

Originally this infrastructure would only host:

• Personal website

• VPN

• Small Docker environment

The vision expanded significantly afterwards.

Status

Completed.

---

## Decision 004

### CHOMS-HOMELAB became CHOMS Platform

Initially the project was described as a Homelab.

As the roadmap evolved it became clear that infrastructure represented only one component of a much larger ecosystem.

The project therefore stopped being viewed as a Homelab.

It became an engineering platform.

This conceptual change influenced every subsequent architectural decision.

Status

Completed.

---

## Decision 005

### Enterprise methodology before enterprise hardware

One of the most important strategic decisions was deliberately applying enterprise engineering practices to inexpensive hardware.

The objective was never to imitate a datacenter.

The objective was to demonstrate that engineering maturity depends on methodology rather than budget.

Professional documentation.

Architecture.

Versioning.

Operational procedures.

Change management.

These principles became mandatory from the beginning.

Status

Permanent.

---

## Decision 006

### Phase-based development

Rather than attempting to build everything at once, the project adopted phased evolution.

Each phase represents a complete engineering milestone.

Each completed phase becomes the stable foundation for the next.

This approach reduces technical debt while allowing the roadmap to evolve naturally.

Status

Permanent.

---

## Decision 007

### Dedicated NAS architecture

Originally every compute node was expected to store its own data.

As future clustering and shared services were discussed, this approach proved insufficient.

Several alternatives were evaluated.

### Local disks on every node

Advantages

Simple.

No additional hardware.

Fast local access.

Problems

Data fragmentation.

Poor scalability.

Complicated backups.

No shared storage.

Decision

Rejected.

---

### Commercial NAS

Several commercial NAS appliances were considered.

Advantages

Professional software.

Easy administration.

Reliable hardware.

Problems

Higher acquisition cost.

Vendor lock-in.

Limited hardware flexibility.

Lower educational value.

Decision

Rejected for the current project stage.

---

### Repurposed desktop tower

During the hardware inventory an unused desktop tower became available.

Characteristics included:

• Intel Core i5 processor.

• Six native SATA ports.

• Standard ATX motherboard.

• Expandable RAM.

• PCI Express slots.

• Existing power supply.

• Multiple drive bays.

Instead of purchasing a commercial NAS, the decision was made to transform this existing computer into the future storage server.

This perfectly matched one of the project's core engineering principles:

Reuse before replacing.

Decision

Accepted.

Current planned configuration:

Operating System

120 GB SSD

Storage Pool

Five mechanical HDDs.

Future capabilities:

Shared storage.

Snapshots.

Backup repository.

Virtual machine storage.

Container persistent volumes.

Long-term archive.

Future RAID.

Future replication.

Status

Planned for Phase 2.

---

## Decision 008

### Hardware standardisation

Several hardware platforms were evaluated.

Including:

Lenovo ThinkCentre M710q

Lenovo ThinkCentre M720q

Lenovo M93p

Mac Pro 2009

Mac Pro 2013

iMac

ASUS Mini PCs

Raspberry Pi

Rather than purchasing random equipment, the objective became standardising compute nodes.

Current preference favours Lenovo Tiny systems because they provide:

Excellent performance per euro.

DDR4 support.

NVMe compatibility.

Low power consumption.

Compact form factor.

Excellent Linux compatibility.

Strong availability in the second-hand market.

This decision is expected to simplify future cluster management.

Status

In progress.

---

## Decision 009

### Raspberry Pi role

Instead of acting as a compute node, the Raspberry Pi is expected to become a specialised infrastructure appliance.

Potential responsibilities include:

Infrastructure monitoring.

DNS.

VPN.

Automation.

Network services.

Management services.

Its low power consumption makes it an excellent candidate for always-on operational tasks.

Status

Planned.

---

# Lessons learned

Several important lessons have already emerged.

The roadmap will always evolve.

Hardware matters less than architecture.

Documentation is far more valuable than expected.

Planning reduces future complexity.

Professional engineering can be achieved using inexpensive equipment.

Infrastructure should always support future business objectives.

Engineering decisions should always be recorded.

---

# Looking ahead

This document is intentionally unfinished.

Every important hardware evaluation.

Every architecture review.

Every technology migration.

Every rejected idea.

Every strategic change.

Every lesson learned.

Should eventually become part of this engineering memory.

The platform will continue changing.

This document ensures that its history is never lost.
