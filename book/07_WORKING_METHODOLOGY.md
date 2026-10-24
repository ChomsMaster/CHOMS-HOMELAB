# Working Methodology

## Introduction

Technology alone does not build reliable platforms.

Methodology does.

One of the primary objectives of CHOMS Platform is not simply to build infrastructure, but to demonstrate the engineering discipline required to design, implement, operate and continuously evolve complex systems.

For that reason, this project follows a structured engineering methodology inspired by enterprise software development, infrastructure engineering and operational excellence.

Although adapted for an independent project, the principles are intentionally aligned with professional practices used in large organisations.

---

# Engineering principles

Every activity performed within CHOMS Platform follows a small set of non-negotiable principles.

These principles influence every architectural decision, every implementation and every future phase.

The principles are:

• Understand before implementing.

• Document before forgetting.

• Design before building.

• Automate before repeating.

• Measure before optimising.

• Secure before exposing.

• Simplify before expanding.

• Version everything.

• Leave every component better than it was found.

These principles remain valid regardless of the technologies involved.

---

# Methodological influences

CHOMS Platform is not intended to copy a single framework.

Instead, it combines practices inspired by several well-established engineering methodologies.

Among them are:

## ITIL

Used as inspiration for:

- Change Management
- Configuration Management
- Service Lifecycle
- Service Operation
- Continuous Service Improvement

---

## Agile

Applied through:

- Incremental development
- Small deliverables
- Continuous feedback
- Iterative improvements

Rather than attempting to complete the entire platform at once, the project evolves through multiple controlled phases.

---

## Architecture Decision Records (ADR)

Every significant architectural decision should eventually produce an ADR.

The purpose is to preserve engineering reasoning.

Future contributors should understand:

Why a decision was made.

Which alternatives were considered.

Why they were rejected.

What consequences are expected.

---

## DevOps

Operational philosophy includes:

Infrastructure as Code.

Automation.

Version control.

Continuous validation.

Operational repeatability.

Monitoring.

Observability.

Everything should be reproducible.

---

## Site Reliability Engineering (SRE)

Although not implemented completely during early phases, the long-term roadmap incorporates SRE principles including:

Monitoring.

Metrics.

Availability.

Reliability.

Incident analysis.

Postmortems.

Capacity planning.

Operational excellence.

---

# Project lifecycle

Every major feature follows the same lifecycle.

Idea

↓

Analysis

↓

Architecture

↓

Documentation

↓

Implementation

↓

Validation

↓

Operational verification

↓

Documentation update

↓

Git commit

↓

Release

↓

Lessons learned

No implementation should skip these stages unless explicitly justified.

---

# Documentation strategy

Documentation is treated as a first-class engineering asset.

Every major component should answer:

What is it?

Why does it exist?

How does it work?

How is it operated?

How is it recovered?

What are its dependencies?

What risks exist?

How will it evolve?

The objective is to minimise undocumented knowledge.

Knowledge should remain inside the repository rather than inside people's memories.

---

# Phase-based development

CHOMS Platform intentionally evolves through phases.

Each phase represents a complete engineering milestone.

A phase is considered complete only after:

Objectives achieved.

Infrastructure validated.

Documentation updated.

Operational procedures completed.

Repository cleaned.

Version released.

Lessons documented.

Only then does the next phase begin.

---

# Version control

Git is considered the single source of truth.

Every significant change should be committed.

Meaningful commit messages are preferred over generic ones.

Examples:

feat:

fix:

docs:

refactor:

security:

infra:

ops:

test:

release:

Each version should represent a stable point in the project's evolution.

---

# Change management

Every architectural change should answer four questions before implementation.

Why is this change necessary?

What problem does it solve?

Which risks does it introduce?

How can it be reversed?

If these questions cannot be answered clearly, implementation should be postponed.

---

# Decision making

Whenever multiple technical solutions exist, evaluation follows the same order of priority.

1. Maintainability

2. Reliability

3. Scalability

4. Simplicity

5. Performance

6. Cost

This order intentionally prioritises long-term sustainability over short-term optimisation.

---

# Risk management

Every implementation should attempt to reduce one or more categories of risk.

Examples include:

Operational risk.

Security risk.

Data loss.

Vendor lock-in.

Complexity.

Human error.

Knowledge loss.

Future technical debt.

Reducing risk is considered as valuable as adding new functionality.

---

# Operational validation

Every completed implementation should be validated before being considered finished.

Validation includes, whenever applicable:

Service health.

Container status.

Network connectivity.

Authentication.

Backups.

Monitoring.

Logging.

Security.

Documentation.

Recovery procedures.

A feature that cannot be operated reliably is not considered complete.

---

# Continuous improvement

Every completed phase generates new knowledge.

That knowledge should feed the next phase.

Mistakes are expected.

Undocumented mistakes are not.

The platform is expected to improve continuously through iterative refinement.

Every version should leave the project in a better state than the previous one.

---

# Engineering over shortcuts

One of the defining characteristics of CHOMS Platform is the deliberate rejection of unnecessary shortcuts.

Fast implementations are valuable only when they do not compromise long-term quality.

Whenever additional effort significantly improves maintainability, documentation or architectural quality, that effort is considered justified.

The project therefore values engineering excellence above rapid delivery.

---

# Definition of Done

A task is only considered complete when all applicable criteria have been satisfied.

✔ Architecture validated.

✔ Implementation completed.

✔ Documentation updated.

✔ Security reviewed.

✔ Operational checks passed.

✔ Repository cleaned.

✔ Version committed.

✔ Lessons documented.

Only then can the work be considered finished.

---

# Final philosophy

CHOMS Platform is not intended to become another Homelab repository.

It is intended to become a complete engineering case study.

Every phase should demonstrate not only technical capability but also engineering maturity.

The platform should ultimately reflect the same level of discipline expected from professional enterprise environments, regardless of the size of the hardware on which it runs.

Engineering is not determined by budget.

Engineering is determined by methodology.

That principle defines every decision made throughout CHOMS Platform.
