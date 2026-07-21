# Lessons Learned

This document summarizes the main technical challenges encountered during the implementation of the CHOMS-HOMELAB infrastructure and the solutions adopted.

---

# 1. ISP CG-NAT

## Problem

The initial Internet connection was behind CG-NAT, preventing inbound connections from the Internet.

## Solution

The ISP was contacted and the connection was migrated to a public IPv4 address, allowing external access and port forwarding.

---

# 2. Double Router Topology

## Problem

The homelab was initially connected behind a second router operating in router mode, creating a double NAT scenario.

This complicated port forwarding and network routing.

## Solution

The secondary router was converted into Access Point mode.

This simplified the network and allowed all devices to operate within the same LAN.

---

# 3. WireGuard Deployment

## Problem

The initial VPN configuration required several iterations before achieving stable remote connectivity.

DNS resolution and routing required additional adjustments.

## Solution

WireGuard was successfully deployed with persistent connectivity, allowing secure remote administration from mobile devices.

---

# 4. Linux Permissions

## Problem

Executable scripts could not be launched directly.

## Solution

Linux execution permissions and the chmod utility were studied to understand the execution model used by Unix systems.

---

# 5. Docker Networking

## Problem

Understanding Docker bridge networks, container isolation and exposed ports required additional testing.

## Solution

The services were successfully deployed while keeping only the necessary ports exposed to the host.

---

# 6. Infrastructure Documentation

## Problem

The initial documentation lacked structure and scalability.

## Solution

A modular documentation structure was designed, making future expansion significantly easier.

---

# Conclusion

Every issue encountered during this project became an opportunity to improve the infrastructure and strengthen practical knowledge in Linux, networking, Docker and systems administration.

Rather than avoiding technical problems, the project embraces them as part of the engineering process.

