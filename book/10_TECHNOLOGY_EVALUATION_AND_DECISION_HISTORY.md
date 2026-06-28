# Technology Evaluation and Decision History

## Engineering is making decisions

One of the biggest misconceptions in software engineering is believing that engineering consists of writing code or deploying infrastructure.

It does not.

Engineering is primarily the process of making informed decisions.

Every architecture is the result of thousands of decisions.

Some are correct.

Some are temporary.

Some will eventually prove to be mistakes.

What matters is not avoiding mistakes.

What matters is understanding why each decision was made.

For this reason CHOMS Platform documents not only what was implemented, but also what was intentionally rejected.

Future contributors should understand both paths.

---

# Every decision had alternatives

No significant component of CHOMS Platform was selected randomly.

Every major decision follows approximately the same process.

Identify the problem.

↓

Evaluate alternatives.

↓

Compare advantages.

↓

Compare disadvantages.

↓

Estimate future scalability.

↓

Estimate operational complexity.

↓

Select the most appropriate solution.

↓

Document the decision.

This methodology ensures that architectural evolution remains understandable even years later.

---

# Hardware philosophy

Unlike enterprise organisations, CHOMS Platform intentionally began using inexpensive second-hand hardware.

This decision was not driven only by budget.

It was also an engineering challenge.

The objective was to demonstrate that professional engineering practices are independent of hardware cost.

Architecture should not depend upon expensive equipment.

Good engineering remains good engineering regardless of the hardware underneath.

---

# Why second-hand hardware?

The decision was influenced by several factors.

Lower investment.

Reduced financial risk.

Availability.

Excellent performance per euro.

Ability to experiment freely.

Incremental growth.

Easy replacement.

Learning opportunities.

The objective is to grow the infrastructure gradually rather than making a large initial investment.

---

# Hardware evaluated

Throughout the project several different hardware platforms have been analysed.

Each evaluation contributes to future architectural decisions.

Examples include:

Lenovo ThinkCentre M710q

Lenovo ThinkCentre M720q

Lenovo ThinkCentre M900

Lenovo ThinkCentre M93p

ASUS Mini PCs

Custom NAS hardware

Intel-based tower systems

Mac mini

iMac

Mac Pro (2009)

Mac Pro (2013)

Raspberry Pi

Every evaluation considered:

Performance.

Power consumption.

Expandability.

Storage options.

Memory capacity.

Virtualization capabilities.

Operational cost.

Long-term maintainability.

---

# Why Lenovo Tiny became the preferred node

After evaluating multiple alternatives, Lenovo Tiny systems gradually became the preferred choice for future compute nodes.

Reasons include:

Excellent price/performance ratio.

DDR4 memory support.

NVMe support.

Low power consumption.

Enterprise reliability.

Compact design.

Good Linux compatibility.

Large second-hand market.

Easy hardware replacement.

Standardized fleet management.

These characteristics make them particularly attractive for building multi-node infrastructure.

---

# Why some alternatives were rejected

Several alternatives were considered but not selected as primary compute nodes.

Examples include older DDR3 systems.

Although functional, they present limitations regarding:

Future memory upgrades.

Storage performance.

Power efficiency.

Long-term availability.

Similarly, workstation-class systems such as older Mac Pro models offer significant processing capability but consume considerably more power and physical space.

For the long-term platform vision they are better suited to specialised workloads rather than becoming standard infrastructure nodes.

---

# Storage decisions

Storage architecture has also evolved throughout the project.

Initially, local disks were sufficient.

As the platform vision expanded, centralised storage became necessary.

The preferred long-term architecture consists of:

Dedicated NAS.

Independent operating system SSD.

Separate storage pool.

Snapshot capability.

Future replication.

Future redundancy.

Shared storage for compute nodes.

This architecture separates storage responsibilities from compute responsibilities.

It also simplifies maintenance and future expansion.

---

# Why HDD instead of SSD?

Another important engineering decision concerns storage media.

Although SSDs provide significantly higher performance, they are not always the optimal choice for bulk storage.

For the planned NAS:

Large-capacity HDDs provide better cost efficiency.

Sequential performance is sufficient.

Reliability is acceptable.

Replacement costs remain low.

Future expansion becomes easier.

SSDs remain reserved primarily for:

Operating systems.

Virtual machines.

Databases.

Container workloads.

Caching.

This hybrid strategy offers an excellent balance between performance and cost.

---

# Networking evolution

Networking decisions also follow incremental evolution.

The initial platform operates successfully using consumer networking equipment.

Future phases gradually introduce:

Dedicated switches.

VLAN segmentation.

Enterprise routing.

Higher bandwidth.

Improved monitoring.

Network redundancy.

Professional firewall policies.

Infrastructure therefore grows alongside operational requirements.

There is no benefit in introducing unnecessary complexity before it becomes valuable.

---

# Technology is temporary

One of the most important engineering principles adopted by CHOMS Platform is that technologies are replaceable.

Architectural principles are not.

Docker may eventually be replaced.

Kubernetes may eventually evolve.

Operating systems may change.

Monitoring stacks may change.

Storage technologies may change.

The platform is intentionally designed so that individual technologies can evolve without forcing complete architectural redesign.

---

# Every rejected idea matters

One of the goals of this document is preserving engineering history.

Knowing why something was rejected is often as valuable as knowing why something was accepted.

Future versions of the platform may revisit previously discarded technologies under different circumstances.

When that happens, the original engineering reasoning remains available.

No decision should disappear simply because another one was implemented.

---

# Engineering memory

This document is expected to grow continuously.

Every major technology evaluation.

Every hardware comparison.

Every architectural trade-off.

Every rejected alternative.

Every future migration.

All become part of the engineering memory of CHOMS Platform.

Good engineering is not only about making decisions.

It is about remembering why those decisions were made.
