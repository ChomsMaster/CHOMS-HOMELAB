---
## Project Information

**Project Name**

CHOMS-HOMELAB

**Owner**

Oscar Salcedo

Founder

CHOMS Master Technology Services

Future Contact

[oscar.salcedo@chomsmaster.com](mailto:oscar.salcedo@chomsmaster.com)

Repository

[https://github.com/ChomsMaster/CHOMS-HOMELAB](https://github.com/ChomsMaster/CHOMS-HOMELAB)

---

# Executive Summary

CHOMS-HOMELAB is a self-hosted infrastructure platform built from scratch as a long-term engineering project.

The project started as a practical solution to eliminate recurring hosting costs after personal financial circumstances made commercial hosting and domain subscriptions difficult to maintain.

Instead of migrating to another hosting provider, the decision was made to design and build a complete on-premise infrastructure using a low-cost Mini PC.

As the platform evolved, the objective expanded beyond replacing hosting services.

Today the project serves four independent purposes:

• Production-inspired infrastructure

• Professional engineering portfolio

• Continuous Linux / DevOps learning platform

• Foundation for future CHOMS Master infrastructure services

The project follows one simple philosophy:

> Build once.
> Document everything.
> Recreate anytime.

---

# Project Vision

The long-term objective is not simply to own a home server.

The objective is to create a maintainable infrastructure capable of hosting personal, business and development services while following professional engineering practices.

Every deployed service must satisfy three conditions:

• Solve a real problem

• Be fully documented

• Be reproducible from scratch

---

# Initial Problem

Commercial hosting was discontinued due to cost optimization.

Instead of continuing to pay monthly hosting and cloud services, the decision was made to invest in a permanent infrastructure that could gradually replace external providers.

The project therefore evolved from:

Hosting replacement

into

Complete Self-Hosted Infrastructure Platform.

---

# Long-Term Objectives

Infrastructure

• Secure self-hosted environment

• Full remote administration

• Centralized services

• Private cloud

• Internal APIs

• Monitoring

• Automated backups

Professional Growth

• Linux administration

• Docker

• Networking

• Security

• DevOps

• Backend Engineering

• Infrastructure Documentation

Portfolio

The repository is intentionally designed to demonstrate engineering methodology rather than software installation.

Documentation quality is considered as important as implementation.

---

# Current Infrastructure

Hardware

ACEPC AK2 Mini PC

Intel Celeron J3455

6 GB RAM

128 GB SSD (Operating System)

120 GB SSD (/data)

Operating System

Debian 13 (Trixie)

Storage Layout

/

Operating System

/data

Persistent storage

/data/projects/choms-homelab

Infrastructure

/projects

Repositories

/backups

System backups

---

# Current Services

Infrastructure

Docker

Docker Compose

Networking

WireGuard VPN

DNS

Pi-hole

Web

Nginx

Database

PostgreSQL 17

Security

UFW

Fail2ban

---

# Network Architecture

LAN

192.168.1.138

VPN

10.10.10.0/24

Remote Access

WireGuard

Router Topology

Internet

↓

Main Router

↓

Access Point

↓

CHOMS-HOMELAB

The secondary router was intentionally converted into an Access Point to avoid double NAT and simplify VPN deployment.

---

# Storage Architecture

System SSD

Operating system

Application binaries

Docker Engine

Second SSD

Persistent Docker volumes

Future Nextcloud storage

Backups

Repositories

Databases

This separation allows complete operating system reinstallation without losing application data.

---

# Docker Philosophy

Applications are deployed as isolated containers whenever possible.

Advantages

Easy upgrades

Simple rollback

Version control

Service isolation

Rapid disaster recovery

Native installation is reserved only for operating system components.

---

# Security Philosophy

Minimal exposed services

Default deny firewall

VPN-first administration

Fail2ban protection

Local-only PostgreSQL

No unnecessary public ports

Documentation before deployment

---

# Engineering Decisions

Decision 001

Operating System

Debian selected over Ubuntu due to stability, predictable updates and lower resource usage.

Decision 002

Container Platform

Docker Compose selected for simplicity, reproducibility and maintainability.

Decision 003

Storage

Dedicated SSD mounted as /data to separate operating system from persistent information.

Decision 004

VPN

WireGuard selected due to performance and modern cryptography.

Decision 005

Database

PostgreSQL only accessible from localhost.

Decision 006

Repository

Every significant infrastructure change must be versioned through Git.

---

# Repository Philosophy

The repository is not intended to store configuration files only.

It documents:

Architecture

Deployment

Engineering decisions

Recovery procedures

Lessons learned

Operational scripts

Project evolution

---

# Documentation Structure

README

Project presentation

docs/

Technical documentation

scripts/

Operational automation

diagrams/

Architecture diagrams

assets/

Images

CHANGELOG

Project history

LICENSE

Licensing

---

# Operational Scripts

Health Check

System validation

Base Installation

Server Structure

Docker Installation

Firewall Configuration

Storage Configuration

WireGuard Deployment

Nginx Deployment

PostgreSQL Deployment

Pi-hole Deployment

Backup

System Update

Server Restore Guide

---

# Lessons Learned

Always document before expanding.

Avoid duplicated scripts.

Version every significant change.

Keep services isolated.

Separate system from data.

Prefer reproducible deployments.

Always verify repository structure before creating new files.

Test before documenting.

---

# Current Status

Infrastructure

Approximately 80–85% complete.

Current Focus

Repository professionalization.

Documentation.

Architecture diagrams.

Operational automation.

Upcoming Services

Reverse Proxy

Nextcloud

Mail Server

Monitoring

FastAPI

CHOMS Dashboard

CHOMS Master API

Future Infrastructure Integrations

---

# Future Vision

CHOMS-HOMELAB will become the central infrastructure for all CHOMS Master services.

The platform will eventually provide:

Personal Cloud

Business Hosting

Mail Server

Internal APIs

Monitoring

Administration Dashboard

Backend Infrastructure Services

CI/CD

Automation

Remote Infrastructure Management

---

# Project Philosophy

This project is intentionally built without shortcuts.

Every deployment is executed manually before automation.

Every service is understood before abstraction.

Every architectural decision is documented.

The goal is not only to build infrastructure.

The goal is to become capable of designing, operating, documenting and maintaining production-quality systems.

---

# Engineering Journal

2026-06

Project started.

Debian installed.

Docker deployed.

WireGuard configured.

Router migrated to Access Point.

Pi-hole deployed.

Nginx deployed.

PostgreSQL deployed.

GitHub repository created.

Documentation standardized.

Operational scripts implemented.

Repository reorganized.

Project transitioned from a personal laboratory into a professional engineering portfolio.


