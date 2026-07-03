# CHOMS Platform - Node Lifecycle

**Status:** Draft  
**Phase:** Phase 2 - Multi-node readiness  
**Owner:** Oscar Salcedo  

---

## 1. Purpose

This document defines how a new compute node is introduced into CHOMS Platform.

The objective is to avoid treating each server as a one-off machine. Every node must follow a predictable lifecycle so the platform can scale from one node to many nodes without redesigning the infrastructure.

---

## 2. Node Lifecycle

```text
Hardware acquired
        ↓
Debian installed
        ↓
Hostname assigned
        ↓
Network identity confirmed
        ↓
Base packages installed
        ↓
Firewall baseline applied
        ↓
Docker installed
        ↓
Storage access prepared
        ↓
Healthcheck executed
        ↓
Node documented
        ↓
Role assigned
        ↓
Node accepted into platform
