# CHOMS Platform

# Network Architecture

**Version:** 1.0

**Status:** Living Document

**Owner:** Oscar Manuel Salcedo Chirinos

---

# 1. Purpose

This document defines the network architecture of CHOMS Platform.

Networking provides the communication layer that connects every physical device, application, service and external user.

Its objective is to deliver secure, reliable and scalable connectivity while maintaining operational simplicity.

The network architecture has been designed to support the current infrastructure while remaining prepared for future enterprise-level expansion.

---

# 2. Objectives

The networking strategy pursues several long-term objectives.

* Secure internal communication.
* Controlled external access.
* Remote administration.
* Network segmentation.
* High availability readiness.
* Infrastructure scalability.
* Service discovery.
* Secure VPN connectivity.
* Future multi-site connectivity.

---

# 3. Design Philosophy

Networking is considered an infrastructure service rather than a collection of independent devices.

Every network component contributes to a single, unified platform.

The architecture follows several principles.

Simplicity before complexity.

Security before convenience.

Standardisation before improvisation.

Scalability before optimisation.

Every modification should improve the overall architecture rather than solve isolated problems.

---

# 4. Network Layers

The infrastructure is logically divided into multiple layers.

## Physical Network

Switches.

Ethernet cabling.

Routers.

Internet connectivity.

Network Interface Cards.

---

## Transport Layer

IPv4 networking.

Future IPv6 support.

TCP.

UDP.

Routing.

---

## Infrastructure Services

DNS.

DHCP.

Reverse Proxy.

VPN.

Certificate management.

Authentication.

Monitoring.

---

## Application Layer

Web applications.

APIs.

Media services.

Private cloud.

Development services.

Internal tools.

---

# 5. Internal Network

All infrastructure components communicate through a private local network.

Internal communication should never require public Internet access.

Examples include:

Docker services.

Databases.

Monitoring.

Authentication.

Storage.

Application servers.

Internal traffic remains isolated whenever possible.

---

# 6. External Access

External users never communicate directly with internal services.

All incoming requests pass through a controlled entry point.

Current architecture:

Internet

↓

Router

↓

Reverse Proxy

↓

Authentication (when required)

↓

Application Service

This architecture centralises access control while simplifying security management.

---

# 7. Reverse Proxy

The reverse proxy is responsible for:

HTTP routing.

HTTPS termination.

Automatic certificates.

Load balancing (future).

Service publishing.

Domain management.

Traffic redirection.

The reverse proxy becomes the primary gateway into CHOMS Platform.

---

# 8. DNS Strategy

The platform maintains both internal and external name resolution.

Internal DNS simplifies service discovery.

External DNS exposes public services.

Future objectives include:

Split DNS.

Internal service names.

Automatic service registration.

Multi-site support.

---

# 9. VPN Architecture

The VPN is one of the foundational services of CHOMS Platform.

The original motivation for the project emerged from the need to securely connect infrastructure located in Spain and Venezuela.

The long-term architecture includes secure VPN endpoints in both countries.

Primary objectives include:

Secure remote administration.

Private access to internal services.

Cross-country connectivity.

Geographical access to regional services.

Encrypted communications.

Future site-to-site networking.

The VPN remains one of the strategic pillars of the platform.

---

# 10. Network Security

Security is applied throughout every network layer.

Primary mechanisms include:

HTTPS.

Encrypted tunnels.

Authentication.

Least privilege.

Firewall policies.

Certificate management.

Traffic isolation.

Continuous monitoring.

Security should never rely on a single control mechanism.

Instead, multiple defensive layers provide protection.

---

# 11. Service Discovery

Infrastructure services should communicate using logical service names rather than fixed IP addresses whenever practical.

Examples include:

PostgreSQL.

Nextcloud.

Grafana.

Jellyfin.

Authelia.

Traefik.

This simplifies migration and future scaling.

---

# 12. Future Evolution

The network architecture is intentionally designed for continuous growth.

Future capabilities include:

VLAN segmentation.

Dedicated management network.

Storage network.

Cluster networking.

Kubernetes networking.

Multiple Internet providers.

High Availability.

Site-to-site VPN.

Remote infrastructure.

IPv6 deployment.

Enterprise switching.

Network redundancy.

---

# 13. Relationship with Other Domains

The networking architecture supports every major component of CHOMS Platform.

Storage Architecture.

Compute Architecture.

Security Architecture.

Observability Architecture.

High Availability.

Disaster Recovery.

No subsystem exists independently from the network.

Networking therefore becomes the foundation that connects every architectural domain.

---

# Engineering Principles

Networking decisions within CHOMS Platform follow several principles.

Internal traffic remains private whenever possible.

External exposure should be minimised.

Every exposed service must be authenticated unless explicitly intended for public access.

Infrastructure services communicate using predictable addressing.

Network complexity should increase only when justified by operational value.

Documentation accompanies every significant networking change.

---

# Long-Term Vision

The networking architecture is expected to evolve from a simple home network into a small enterprise infrastructure.

While the physical scale may remain modest, the architectural principles remain identical.

Future infrastructure should provide:

Reliable connectivity.

Secure communications.

Remote administration.

Scalable service publishing.

Multi-site integration.

Enterprise-grade operational practices.

The objective is not simply to connect machines.

The objective is to build a resilient communications platform capable of supporting every future initiative within CHOMS Platform.

---

# Final Statement

Networking is more than cables, switches and IP addresses.

It is the communication fabric that enables every service, every application and every engineering capability within CHOMS Platform.

Every future networking decision should reinforce simplicity, security, scalability and long-term maintainability.
