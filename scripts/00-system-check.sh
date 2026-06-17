#!/bin/bash

echo "=== CHOMS-HOMELAB SYSTEM CHECK ==="

echo
echo "[Hostname]"
hostname

echo
echo "[Current user]"
whoami

echo
echo "[OS]"
cat /etc/os-release | grep -E "PRETTY_NAME|VERSION"

echo
echo "[IP addresses]"
hostname -I

echo
echo "[Disk usage]"
df -h

echo
echo "[Memory]"
free -h

echo
echo "[Docker]"
docker --version 2>/dev/null || echo "Docker not installed"

echo
echo "[Docker Compose]"
docker compose version 2>/dev/null || echo "Docker Compose not installed"

echo
echo "[Git]"
git --version 2>/dev/null || echo "Git not installed"

echo
echo "[GitHub CLI]"
gh --version 2>/dev/null || echo "GitHub CLI not installed"

echo
echo "[WireGuard]"
wg --version 2>/dev/null || echo "WireGuard not installed"

echo
echo "[UFW]"
sudo ufw status verbose 2>/dev/null || echo "UFW not available"

echo
echo "[Fail2ban]"
systemctl is-active fail2ban 2>/dev/null || echo "Fail2ban not active"

echo
echo "[Docker containers]"
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" 2>/dev/null

echo
echo "=== CHECK COMPLETE ==="
