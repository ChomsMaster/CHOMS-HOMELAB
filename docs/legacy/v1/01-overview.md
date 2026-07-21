# Project Overview

## Introduction

CHOMS-HOMELAB is a self-hosted infrastructure platform created to replace traditional hosting services with a fully controlled environment built on open-source technologies.

The project originated from a practical need. After maintaining a personal website through a commercial hosting provider, recurring costs eventually outweighed the actual requirements of the platform. Rather than continuing to rent external infrastructure, the decision was made to build and manage an independent environment using affordable hardware.

What initially started as a simple web hosting replacement quickly evolved into a complete infrastructure project covering networking, Linux administration, Docker containers, secure remote access, databases and future cloud services.

Today, the homelab serves both as production infrastructure for personal services and as a continuous learning platform where new technologies can be deployed, tested and documented under real operating conditions.

---

# Project Objectives

The platform has been designed with the following objectives:

* Build and maintain a secure self-hosted infrastructure.
* Reduce dependency on commercial hosting providers.
* Gain practical experience in Linux systems administration.
* Centralize multiple services under a single platform.
* Develop backend and infrastructure engineering skills.
* Document every implementation as part of a professional portfolio.

---

# Design Philosophy

The project follows a number of fundamental principles.

## Simplicity

Only technologies that provide real value are introduced.

## Security

Services are deployed following a security-first approach, minimizing unnecessary exposure to the Internet.

## Documentation

Every architectural decision is documented to ensure the platform remains understandable and maintainable over time.

## Scalability

Although the current deployment runs on modest hardware, the architecture allows migration to more powerful hardware or cloud environments with minimal changes.

---

# Current Scope

The current platform includes:

* Debian Linux
* Docker
* WireGuard VPN
* Pi-hole
* Nginx
* PostgreSQL
* Local backup storage
* GitHub documentation

Future services will include private cloud storage, monitoring, reverse proxy, backend APIs and infrastructure supporting future CHOMS Master services.

