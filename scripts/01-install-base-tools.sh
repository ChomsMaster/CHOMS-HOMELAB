#!/bin/bash

source "$(dirname "$0")/lib/common.sh"

set -e
echo "Installing base tools..."

if command_exists docker; then
    success "Base tools already installed."
    exit 0
fi
sudo apt update

sudo apt install -y \
  curl \
  wget \
  nano \
  tree \
  git \
  gh \
  ufw \
  fail2ban \
  wireguard \
  wireguard-tools \
  qrencode \
  traceroute \
  dnsutils \
  htop \
  unzip \
  ca-certificates \
  gnupg \
  lsb-release

echo "Base tools installed."
