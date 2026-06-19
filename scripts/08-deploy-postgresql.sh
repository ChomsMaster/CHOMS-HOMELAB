#!/bin/bash
set -e

echo "Deploying PostgreSQL..."

APP_DIR="/data/projects/choms-homelab/docker"
DATA_DIR="/data/postgres"

DB_NAME="choms_lab"
DB_USER="choms_admin"

sudo mkdir -p "$APP_DIR"
sudo mkdir -p "$DATA_DIR"

sudo chown -R "$USER:$USER" "$APP_DIR"
sudo chown -R "$USER:$USER" "$DATA_DIR"

echo
echo "Enter PostgreSQL password:"
read -s DB_PASSWORD

cat > "$APP_DIR/compose.yml" <<YAML
services:
  postgres:
    image: postgres:17
    container_name: choms-postgres
    restart: unless-stopped

    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}

    ports:
      - "127.0.0.1:5432:5432"

    volumes:
      - ${DATA_DIR}:/var/lib/postgresql/data
YAML

cd "$APP_DIR"

DB_NAME=$DB_NAME \
DB_USER=$DB_USER \
DB_PASSWORD=$DB_PASSWORD \
docker compose up -d

echo
echo "Waiting for PostgreSQL..."
sleep 10

docker exec choms-postgres psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();"

echo
echo "PostgreSQL successfully deployed."
