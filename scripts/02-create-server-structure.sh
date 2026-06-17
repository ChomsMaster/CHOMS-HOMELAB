#!/bin/bash
set -e

echo "Creating CHOMS server directory structure..."

sudo mkdir -p /opt/choms/backups
sudo mkdir -p /opt/choms/data
sudo mkdir -p /opt/choms/docker
sudo mkdir -p /opt/choms/projects

sudo mkdir -p /data/backups
sudo mkdir -p /data/postgres
sudo mkdir -p /data/websites
sudo mkdir -p /data/nextcloud

echo "Directory structure created."
