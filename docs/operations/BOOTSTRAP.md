# CHOMS Bootstrap

Every node bootstrap performs:

- Install required packages
- Install Docker
- Install Docker Compose
- Configure CHOMS directories
- Install CHOMS Node Agent
- Enable systemd timer
- Configure node role

Bootstrap scripts:

- scripts/10-bootstrap-edge.sh
- scripts/20-bootstrap-app-node.sh
- scripts/30-bootstrap-storage.sh

The Node Agent is installed automatically during bootstrap.

The Edge bootstrap additionally installs:

- Public DDNS updater
- Reverse Proxy
- VPN
