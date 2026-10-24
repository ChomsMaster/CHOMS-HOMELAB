#!/bin/bash
set -e

echo "Configuring UFW firewall..."

sudo apt update
sudo apt install -y ufw fail2ban

# Default firewall policy
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw default deny routed

# Allow SSH
sudo ufw allow 22/tcp

# Allow WireGuard
sudo ufw allow 51820/udp

# Optional internal test web port
sudo ufw allow 8080/tcp

# Enable firewall
sudo ufw --force enable

# Enable Fail2ban
sudo systemctl enable --now fail2ban

echo "Firewall configured."
echo
sudo ufw status verbose
echo
systemctl is-active fail2ban
