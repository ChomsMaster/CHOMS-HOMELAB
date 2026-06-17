#!/bin/bash

set -e

echo "=== Installing base tools ==="

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
  qrencode \
  traceroute \
  dnsutils \
  htop \
  unzip \
  ca-certificates \
  gnupg

echo "=== Base tools installed ==="
