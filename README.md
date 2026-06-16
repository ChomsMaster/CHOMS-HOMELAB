# CHOMS-HOMELAB

Self-hosted infrastructure project developed and maintained by **Oscar Salcedo**, founder of **CHOMS Master Technology Services**.

## Background

CHOMS Master previously relied on traditional hosting services for its online presence. After discontinuing those services for financial reasons, the project was rebuilt from scratch using affordable hardware and open-source technologies.

The initial goal was simple: recover control over basic services such as web hosting and remote access without depending entirely on external hosting providers.

The result is a small but functional homelab environment used for infrastructure learning, service hosting, backend development and future business services.

## Objectives

- Build a low-cost self-hosted infrastructure.
- Provide secure remote access through VPN.
- Host internal and public-facing services.
- Use Docker for service deployment.
- Maintain clear technical documentation.
- Create a practical portfolio for backend, Linux and infrastructure work.

## Current Stack

- Debian 13
- Docker
- Docker Compose
- Nginx
- WireGuard
- Pi-hole
- PostgreSQL 17
- UFW
- Fail2ban
- GitHub CLI

## Current Services

- VPN access with WireGuard
- DNS filtering with Pi-hole
- Web service test with Nginx
- PostgreSQL database service
- Firewall and intrusion protection
- GitHub-based documentation

## Hardware

Current deployment runs on:

- ACEPC AK2 Mini PC
- Intel Celeron J3455
- 6 GB RAM
- 128 GB SSD for the operating system
- 120 GB SSD for service data

## Documentation

Technical documentation is available in the `docs/` directory:

- `01-overview.md`
- `02-hardware.md`
- `03-network.md`
- `04-security.md`
- `05-wireguard.md`
- `06-pihole.md`
- `07-docker-services.md`
- `08-postgresql.md`
- `09-backup.md`
- `10-roadmap.md`

## Roadmap

Planned improvements include:

- CHOMS Master website
- Corporate email using the CHOMS Master domain
- Private cloud services
- FastAPI backend environment
- Monitoring and automation
- Infrastructure support for future projects such as ShiftCore

## Author

**Oscar Salcedo**  
Founder, CHOMS Master Technology Services  
GitHub: https://github.com/ChomsMaster  
Email: Oscar.Salcedo@chomsmaster.com
