# Network Architecture

## Overview

The network architecture has been designed to provide secure remote access while keeping the internal infrastructure isolated from the public Internet.

The platform is connected behind a DIGI residential Internet connection and uses WireGuard VPN for secure administration and access to internal services.

---

# Physical Topology

```
Internet
     │
     ▼
DIGI Router
     │
     ▼
ACEPC AK2
CHOMS-HOMELAB
192.168.1.138
```

---

# Internal Network

| Network        | Purpose       |
| -------------- | ------------- |
| 192.168.1.0/24 | Local LAN     |
| 10.10.10.0/24  | WireGuard VPN |

---

# Remote Access

Remote administration is performed exclusively through WireGuard VPN.

Once connected, clients gain secure access to internal services without exposing management interfaces directly to the Internet.

Current services available through the VPN include:

* SSH
* Pi-hole
* PostgreSQL (internal)
* Docker services
* Future administration interfaces

---

# Port Forwarding

Only the WireGuard service is exposed through the residential router.

| Port      | Service       |
| --------- | ------------- |
| 51820/UDP | WireGuard VPN |

Additional services will be published only when required and protected behind a reverse proxy.

---

# Network Design Principles

The network follows several design principles:

* Minimize exposed services.
* Prefer VPN access over public administration.
* Keep infrastructure isolated.
* Document every network change.
* Design for future scalability.

---

# Future Improvements

Planned networking enhancements include:

* Reverse proxy
* HTTPS for public services
* Dynamic DNS
* VLAN segmentation (future hardware)
* Centralized monitoring
* Intrusion detection

