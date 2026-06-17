#!/bin/bash
set -e

echo "Deploying Pi-hole..."

APP_DIR="/opt/choms/docker/pihole"

sudo mkdir -p "$APP_DIR"
sudo mkdir -p "$APP_DIR/etc-pihole"
sudo mkdir -p "$APP_DIR/etc-dnsmasq.d"

sudo chown -R "$USER:$USER" "$APP_DIR"

echo
echo "Choose an admin password:"
read -s WEBPASSWORD

cat > "$APP_DIR/compose.yml" <<YAML
services:

  pihole:

    container_name: pihole

    image: pihole/pihole:latest

    restart: unless-stopped

    environment:
      TZ: Europe/Madrid
      WEBPASSWORD: ${WEBPASSWORD}

    ports:
      - "53:53/tcp"
      - "53:53/udp"
      - "8081:80/tcp"

    volumes:
      - ./etc-pihole:/etc/pihole
      - ./etc-dnsmasq.d:/etc/dnsmasq.d
YAML

cd "$APP_DIR"

WEBPASSWORD=$WEBPASSWORD docker compose up -d

echo
echo "Pi-hole deployed."
echo
echo "Open:"
echo
echo "http://SERVER_IP:8081/admin"
