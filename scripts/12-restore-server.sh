#!/bin/bash

echo "CHOMS-HOMELAB Restore Procedure"
echo
echo "This script is intentionally non-destructive."
echo
echo "Manual recovery steps:"
echo
echo "1. Install Debian 13."
echo "2. Clone CHOMS-HOMELAB repository."
echo "3. Run scripts/01-install-base-tools.sh."
echo "4. Run scripts/03-install-docker.sh."
echo "5. Run scripts/04-setup-firewall.sh."
echo "6. Restore /data from backup."
echo "7. Restore /opt/choms/docker compose files."
echo "8. Restore WireGuard configuration manually."
echo "9. Start Docker stacks with docker compose up -d."
echo "10. Validate with scripts/00-healthcheck.sh."
echo
echo "Future versions will include guided restore automation."
