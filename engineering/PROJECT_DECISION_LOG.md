# CHOMS Platform

# Project Decision Log

## Purpose

Engineering is the continuous process of making informed decisions.

Every significant architectural, operational or technological decision taken throughout CHOMS Platform is recorded in this document.

Its purpose is to provide a single source of truth describing how the platform evolved over time.

Each decision receives a unique identifier.

Detailed analysis may be documented separately when required.

---

# Decision Status

The following status values are used throughout the project.

| Status      | Description                           |
| ----------- | ------------------------------------- |
| Proposed    | Idea under evaluation                 |
| Accepted    | Approved and part of the platform     |
| Implemented | Fully deployed                        |
| Rejected    | Evaluated but intentionally discarded |
| Deprecated  | Previously used but replaced          |
| Planned     | Scheduled for a future phase          |

---

# Decision Log

---

## D-001

**Title**

ShiftCore becomes the initial project vision.

**Date**

2026

**Status**

Implemented

**Summary**

The original objective focused on building ShiftCore before any infrastructure existed.

---

## D-002

**Title**

Deploy VPN infrastructure.

**Date**

2026

**Status**

Implemented

**Summary**

VPN services between Spain and Venezuela become the first real infrastructure project.

---

## D-003

**Title**

Build a Homelab instead of renting hosting.

**Status**

Implemented

**Summary**

Commercial hosting is abandoned in favour of self-hosted infrastructure.

---

## D-004

**Title**

Rename the project from CHOMS-HOMELAB to CHOMS Platform.

**Status**

Accepted

**Summary**

Infrastructure evolves into a long-term engineering platform.

---

## D-005

**Title**

Apply enterprise engineering methodology.

**Status**

Implemented

**Summary**

The project adopts enterprise-level documentation, architecture and governance practices despite using commodity hardware.

---

## D-006

**Title**

Develop the platform in engineering phases.

**Status**

Implemented

**Summary**

Incremental phased delivery becomes mandatory for every major milestone.

---

## D-007

**Title**

Reuse an existing desktop tower as the future NAS.

**Status**

Accepted

**Summary**

Instead of purchasing a commercial NAS, an existing Intel Core i5 desktop with six SATA ports is selected to become the dedicated storage server.

---

## D-008

**Title**

Separate compute from storage.

**Status**

Accepted

**Summary**

Persistent storage is removed from compute nodes and centralised within the NAS architecture.

---

## D-009

**Title**

Standardise compute nodes.

**Status**

Accepted

**Summary**

Future compute infrastructure will be standardised around Lenovo Tiny systems to simplify operations and maintenance.

---

## D-010

**Title**

Use Raspberry Pi for infrastructure services.

**Status**

Planned

**Summary**

The Raspberry Pi will host lightweight infrastructure services such as DNS, VPN or automation.

---

## D-011

**Title**

Commercial NAS appliances.

**Status**

Rejected

**Summary**

Commercial NAS solutions were rejected because the educational value and flexibility of building the storage server internally were considered more valuable.

---

## D-012

**Title**

Mac Pro as primary infrastructure node.

**Status**

Rejected

**Summary**

Although powerful, Mac Pro systems were rejected as standard nodes due to power consumption, physical size and lack of standardisation.

---

## D-013

**Title**

M93P as standard node.

**Status**

Rejected

**Summary**

Older DDR3-based platforms were discarded in favour of newer DDR4 Lenovo Tiny systems.

---

## D-014

**Title**

Dedicated NAS operating system.

**Status**

Planned

**Summary**

The NAS will boot from an independent SSD while data remains isolated on dedicated HDD storage pools.

---

## D-015

**Title**

Engineering Book.

**Status**

Implemented

**Summary**

The complete engineering journey of CHOMS Platform is documented as a living technical book alongside the repository.

---

# Engineering Rule

Every architectural decision that significantly changes the platform must appear in this document.

This document represents the historical memory of CHOMS Platform.
