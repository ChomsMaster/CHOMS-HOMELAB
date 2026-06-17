#!/bin/bash
set -e

echo "Deploying Nginx test web service..."

APP_DIR="/opt/choms/docker/nginx"
WEB_DIR="/data/websites/choms-test"

sudo mkdir -p "$APP_DIR"
sudo mkdir -p "$WEB_DIR"

sudo chown -R "$USER:$USER" "$APP_DIR"
sudo chown -R "$USER:$USER" "$WEB_DIR"

cat > "$WEB_DIR/index.html" <<HTML
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>CHOMS-HOMELAB</title>
</head>
<body>
  <h1>CHOMS-HOMELAB operational</h1>
  <p>Nginx test service running from Docker.</p>
</body>
</html>
HTML

cat > "$APP_DIR/compose.yml" <<YAML
services:
  nginx:
    image: nginx:stable-alpine
    container_name: choms-nginx
    restart: unless-stopped
    ports:
      - "8080:80"
    volumes:
      - /data/websites/choms-test:/usr/share/nginx/html:ro
YAML

cd "$APP_DIR"
docker compose up -d

echo "Nginx deployed."
echo "Test URL: http://SERVER_IP:8080"
