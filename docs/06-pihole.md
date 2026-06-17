# Pi-hole

## Overview

Pi-hole provides DNS filtering for the CHOMS-HOMELAB infrastructure.

The service blocks advertisements, trackers and known malicious domains before connections are established, improving privacy and reducing unnecessary network traffic.

Within this project, Pi-hole also serves as a practical exercise in deploying and maintaining containerized network services.

---

# Deployment

Pi-hole is deployed as a Docker container.

Containerization provides:

* Simplified updates
* Service isolation
* Easy backup and recovery
* Consistent deployment

The web administration interface is available only within the trusted network and through the WireGuard VPN.

---

# Network Integration

Pi-hole currently provides DNS services for VPN clients.

Remote devices connected through WireGuard use the local Pi-hole instance for DNS resolution, allowing filtering even when connected from external networks.

This configuration demonstrates how self-hosted services can securely extend beyond the local LAN.

---

# Benefits

The current deployment provides:

* Advertisement blocking
* Tracker blocking
* Improved privacy
* Faster DNS responses through caching
* Centralized DNS management

---

# Design Decisions

Pi-hole was selected because:

* Lightweight resource usage
* Active open-source community
* Excellent Docker support
* Simple administration interface
* Easy integration with WireGuard

---

# Future Improvements

Planned improvements include:

* Custom blocklists
* Local DNS records
* DNS-over-HTTPS evaluation
* High availability experiments
* Statistics dashboard integration

