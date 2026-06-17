# Docker Services

## Overview

Docker is the application platform used throughout the CHOMS-HOMELAB project.

Rather than installing services directly on the operating system, each service runs inside its own isolated container. This approach simplifies deployment, maintenance, updates and future migrations.

The operating system remains clean while applications are managed independently.

---

## Current Services

### Nginx

Purpose:

* Static website hosting
* Reverse proxy (future)
* HTTPS termination (future)

Current Status:

Running

---

### PostgreSQL 17

Purpose:

* Backend databases
* Future FastAPI integration
* Development environment

Current Status:

Running

---

### Pi-hole

Purpose:

* Network-wide DNS filtering
* Advertisement blocking
* DNS management

Current Status:

Running

---

## Why Docker?

The project adopts Docker because it provides several operational advantages:

* Service isolation
* Easy upgrades
* Simple backups
* Fast disaster recovery
* Infrastructure portability
* Reduced operating system pollution

The same containers can be deployed on another Linux server with minimal configuration changes.

---

## Future Services

The Docker platform will eventually host additional infrastructure components, including:

* Nextcloud
* FastAPI services
* Redis
* Grafana
* Prometheus
* Nginx Proxy Manager
* Watchtower
* Portainer (optional)

This architecture allows the infrastructure to grow without changing the underlying operating system.

