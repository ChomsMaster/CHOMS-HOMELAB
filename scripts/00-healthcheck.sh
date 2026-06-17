#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  echo "CHOMS Doctor must be executed with sudo."
  echo
  echo "Run:"
  echo "sudo ./scripts/00-healthcheck.sh"
  exit 1
fi

echo "========================================"
echo "        CHOMS DOCTOR v0.1"
echo "========================================"

echo
echo "[System]"
echo "Hostname: $(hostname)"
echo "User: $(logname 2>/dev/null || echo root)"

echo
echo "[Network]"
echo "IP addresses:"
hostname -I

echo
echo "[Storage]"
df -h / /data 2>/dev/null || df -h

echo
echo "[Memory]"
free -h

echo
echo "[Docker]"
if command -v docker >/dev/null 2>&1; then
  systemctl is-active docker >/dev/null 2>&1 && echo "Docker service: active" || echo "Docker service: inactive"
  docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
else
  echo "Docker not installed"
fi

echo
echo "[WireGuard]"
if command -v wg >/dev/null 2>&1; then
  wg show
else
  echo "WireGuard not installed"
fi

echo
echo "[Firewall]"
if command -v ufw >/dev/null 2>&1; then
  ufw status verbose
else
  echo "UFW not installed"
fi

echo
echo "[Fail2ban]"
if systemctl list-unit-files | grep -q "^fail2ban.service"; then
  echo "Fail2ban: $(systemctl is-active fail2ban)"
else
  echo "Fail2ban not installed"
fi

echo
echo "[PostgreSQL]"
if docker ps --format "{{.Names}}" | grep -q "^choms-postgres$"; then
  echo "PostgreSQL container: running"
else
  echo "PostgreSQL container: not running"
fi

echo
echo "[Pi-hole]"
if docker ps --format "{{.Names}}" | grep -q "^pihole$"; then
  echo "Pi-hole container: running"
else
  echo "Pi-hole container: not running"
fi

echo
echo "[Nginx]"
if docker ps --format "{{.Names}}" | grep -q "^choms-nginx$"; then
  echo "Nginx container: running"
else
  echo "Nginx container: not running"
fi

echo
echo "========================================"
echo "        CHOMS Doctor completed"
echo "========================================"
