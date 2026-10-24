#!/bin/bash
set -e

mkdir -p /data/backups
mkdir -p /data/postgres
mkdir -p /data/websites
mkdir -p /data/nextcloud
mkdir -p /data/docker
mkdir -p /data/projects

chown -R "$SUDO_USER:$SUDO_USER" /data 2>/dev/null || true

echo "Server structure created."
