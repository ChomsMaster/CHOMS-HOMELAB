# WireGuard VPN

## Overview

WireGuard provides secure remote access to the entire CHOMS-HOMELAB infrastructure.

Instead of exposing administrative services directly to the Internet, all remote management is performed through an encrypted VPN tunnel.

This approach significantly reduces the attack surface while allowing full access to internal resources.

---

# Why WireGuard?

Several VPN technologies were evaluated before selecting WireGuard.

The main reasons were:

* Modern cryptography
* Simple configuration
* Excellent performance
* Low resource consumption
* Native support on Linux, Windows, macOS, Android and iOS

For a low-power platform such as the ACEPC AK2, WireGuard offers an excellent balance between security and performance.

---

# Network Design

The VPN uses a dedicated private subnet.

| Network       | Purpose     |
| ------------- | ----------- |
| 10.10.10.0/24 | VPN clients |

The VPN server is hosted directly on Debian instead of inside a Docker container.

This decision simplifies networking, firewall integration and long-term maintenance.

---

# Current Deployment

Current implementation includes:

* WireGuard server running on Debian.
* UDP port forwarding from the residential router.
* iPhone configured as the first VPN client.
* Secure SSH administration through the VPN.
* Internal access to Pi-hole and future services.

---

# Lessons Learned

During deployment, the home network originally contained two routers performing routing functions.

This configuration complicated port forwarding and VPN connectivity.

The solution was to convert the secondary router into an Access Point, simplifying the network and allowing direct communication between the main router and the homelab server.

This change also improved network transparency and simplified future service deployment.

---

# Future Improvements

Planned improvements include:

* Additional client devices.
* QR code generation for mobile onboarding.
* Infrastructure documentation updates.
* Site-to-site VPN experiments.
* IPv6 evaluation.

