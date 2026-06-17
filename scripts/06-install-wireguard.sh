#!/bin/bash
set -e

echo "Installing WireGuard..."

sudo apt update
sudo apt install -y wireguard wireguard-tools qrencode

sudo mkdir -p /etc/wireguard
sudo chmod 700 /etc/wireguard

echo "WireGuard installed."
echo
echo "IMPORTANT:"
echo "- This script installs WireGuard only."
echo "- Server/client keys are NOT generated automatically here."
echo "- Real keys must never be committed to GitHub."
echo
echo "Next manual steps:"
echo "1. Generate server keys."
echo "2. Create /etc/wireguard/wg0.conf."
echo "3. Enable wg-quick@wg0."
echo "4. Configure router UDP 51820 forwarding."
