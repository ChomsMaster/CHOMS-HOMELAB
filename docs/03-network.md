# Architecture

CHOMS-HOMELAB is a self-hosted home server running on Debian 13.

## Core services

- WireGuard: private VPN access
- Pi-hole: DNS filtering
- Docker: container runtime
- Nginx: web service
- UFW: host firewall
- Fail2ban: brute-force protection

## Network

- LAN: 192.168.1.0/24
- Server IP: 192.168.1.138
- VPN network: 10.10.10.0/24
- VPN server: 10.10.10.1
