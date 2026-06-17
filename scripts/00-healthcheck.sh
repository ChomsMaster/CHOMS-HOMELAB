#!/bin/bash

echo "========================================"
echo "      CHOMS-HOMELAB HEALTH CHECK"
echo "========================================"

echo
echo "[Hostname]"
hostname

echo
echo "[IP Addresses]"
hostname -I

echo
echo "[Disk Usage]"
df -h

echo
echo "[Memory]"
free -h

echo
echo "[Docker Containers]"
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" 2>/dev/null || echo "Docker not available"

echo
echo "[WireGuard]"
sudo wg 2>/dev/null || echo "WireGuard not available"

echo
echo "[Firewall]"
sudo ufw status verbose 2>/dev/null || echo "UFW not available"

echo
echo "[Fail2ban]"
systemctl is-active fail2ban 2>/dev/null || echo "Fail2ban not active"

echo
echo "========================================"
echo "Health Check Completed"
echo "========================================"
