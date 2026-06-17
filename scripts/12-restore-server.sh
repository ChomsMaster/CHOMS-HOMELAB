#!/bin/bash
set -e

BACKUP_ROOT="/data/backups"

echo "========================================"
echo " CHOMS-HOMELAB RESTORE ASSISTANT"
echo "========================================"
echo

if [ ! -d "$BACKUP_ROOT" ]; then
  echo "Backup directory not found: $BACKUP_ROOT"
  exit 1
fi

mapfile -t BACKUPS < <(find "$BACKUP_ROOT" -maxdepth 1 -name "choms-homelab_*.tar.gz" | sort -r)

if [ ${#BACKUPS[@]} -eq 0 ]; then
  echo "No backups found in $BACKUP_ROOT"
  exit 0
fi

echo "Available backups:"
echo

for i in "${!BACKUPS[@]}"; do
  echo "$((i+1))) $(basename "${BACKUPS[$i]}")"
done

echo
read -p "Select backup number: " SELECTION

if ! [[ "$SELECTION" =~ ^[0-9]+$ ]]; then
  echo "Invalid selection."
  exit 1
fi

INDEX=$((SELECTION-1))

if [ "$INDEX" -lt 0 ] || [ "$INDEX" -ge "${#BACKUPS[@]}" ]; then
  echo "Selection out of range."
  exit 1
fi

SELECTED="${BACKUPS[$INDEX]}"

echo
echo "Selected backup:"
echo "$SELECTED"
echo

echo "Backup contents:"
tar -tzf "$SELECTED" | head -50

echo
echo "This assistant currently performs safe inspection only."
echo "Automatic restore will be implemented in a future version."
echo
echo "Recommended manual restore order:"
echo "1. Restore repository"
echo "2. Restore Docker compose files"
echo "3. Restore WireGuard configuration"
echo "4. Restore database dump"
echo "5. Restart Docker services"
echo "6. Run scripts/00-healthcheck.sh"
