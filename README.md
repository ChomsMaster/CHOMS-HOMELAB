# CHOMS-HOMELAB

> Self-hosted Infrastructure & Technology Platform

CHOMS-HOMELAB is a self-hosted infrastructure platform designed and maintained as a real-world systems administration, Linux, networking and DevOps engineering project.

The platform centralizes secure remote access, containerized services, databases, DNS filtering, operational scripts, backups, documentation and infrastructure validation.

Rather than being a collection of software installations, the objective is to build, document and maintain a production-inspired environment following professional engineering practices.

---

## Architecture Overview

```mermaid
flowchart TD
    Internet((Internet))
    Router[DIGI Router]
    Server[CHOMS-HOMELAB<br/>Debian 13<br/>192.168.1.138]

    WG[WireGuard VPN<br/>10.10.10.0/24]
    Docker[Docker Engine]
    Nginx[Nginx<br/>Web Service<br/>Port 8080]
    Pihole[Pi-hole<br/>DNS Filtering<br/>Port 8081]
    Postgres[PostgreSQL 17<br/>Localhost only]

    Internet --> Router
    Router --> Server
    Server --> WG
    Server --> Docker
    Docker --> Nginx
    Docker --> Pihole
    Docker --> Postgres

