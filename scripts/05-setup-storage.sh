#!/bin/bash
set -e

echo "Preparing storage layout..."

DATA_DISK="${1:-/dev/sdb}"
DATA_PART="${DATA_DISK}1"

echo "Target disk: $DATA_DISK"
echo
echo "WARNING: This script can format $DATA_PART."
echo "Use only on a clean secondary disk."
echo "Press ENTER to continue or CTRL+C to cancel."
read

sudo mkdir -p /data

if ! lsblk "$DATA_PART" >/dev/null 2>&1; then
  echo "Partition $DATA_PART not found."
  echo "Create the partition manually first with fdisk or parted."
  exit 1
fi

if ! blkid "$DATA_PART" >/dev/null 2>&1; then
  echo "Formatting $DATA_PART as ext4..."
  sudo mkfs.ext4 "$DATA_PART"
else
  echo "$DATA_PART already has a filesystem. Skipping format."
fi

UUID=$(sudo blkid -s UUID -o value "$DATA_PART")

if ! grep -q "$UUID" /etc/fstab; then
  echo "Adding /data mount to /etc/fstab..."
  echo "UUID=$UUID /data ext4 defaults,nofail 0 2" | sudo tee -a /etc/fstab
fi

sudo mount -a

sudo mkdir -p /data/backups
sudo mkdir -p /data/postgres
sudo mkdir -p /data/websites
sudo mkdir -p /data/nextcloud
sudo mkdir -p /data/docker

sudo chown -R "$USER:$USER" /data

echo "Storage ready."
df -h /data
