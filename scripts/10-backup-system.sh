#!/bin/bash
set -e

BACKUP_ROOT="/data/backups"
PROJECT_DIR="/data/projects/choms-homelab"
DATE=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_DIR="$BACKUP_ROOT/choms-homelab_$DATE"

echo "Creating backup in $BACKUP_DIR"

mkdir -p "$BACKUP_DIR"

echo "Backing up repository..."
cp -r "$PROJECT_DIR" "$BACKUP_DIR/repository"

echo "Backing up Docker compose files..."
mkdir -p "$BACKUP_DIR/docker"
cp -r /opt/choms/docker "$BACKUP_DIR/docker" 2>/dev/null || echo "Docker config backup skipped."

echo "Backing up system configuration..."
mkdir -p "$BACKUP_DIR/system"
sudo cp /etc/fstab "$BACKUP_DIR/system/fstab"
sudo cp /etc/ssh/sshd_config "$BACKUP_DIR/system/sshd_config" 2>/dev/null || true
sudo cp -r /etc/wireguard "$BACKUP_DIR/system/wireguard" 2>/dev/null || true
sudo cp -r /etc/fail2ban "$BACKUP_DIR/system/fail2ban" 2>/dev/null || true

echo "Backing up PostgreSQL database..."
mkdir -p "$BACKUP_DIR/databases"
docker exec choms-postgres pg_dump -U choms_admin choms_lab > "$BACKUP_DIR/databases/choms_lab.sql" 2>/dev/null || echo "PostgreSQL backup skipped."

echo "Writing metadata..."
cat > "$BACKUP_DIR/metadata.txt" <<META
Project: CHOMS-HOMELAB
Created: $DATE
Repository: $PROJECT_DIR
Host: $(hostname)
META

echo "Creating archive..."
tar -czf "$BACKUP_DIR.tar.gz" -C "$BACKUP_ROOT" "$(basename "$BACKUP_DIR")"

rm -rf "$BACKUP_DIR"

echo "Backup completed:"
echo "$BACKUP_DIR.tar.gz"
