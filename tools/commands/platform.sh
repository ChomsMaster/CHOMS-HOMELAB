#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="${CHOMS_BASE_DIR:-/data/projects/choms-homelab}"
CONFIG="$BASE_DIR/config/platform/nodes.env"

if [[ ! -f "$CONFIG" ]]; then
  echo "ERROR: platform config not found: $CONFIG"
  exit 1
fi

# shellcheck disable=SC1090
source "$CONFIG"

printf '%s\n' \
  "==============================================" \
  " CHOMS Platform Inventory" \
  "==============================================" \
  "" \
  "Domain: ${CHOMS_DOMAIN}" \
  ""

printf "%-15s %-20s %-15s\n" "ROLE" "NODE" "IP"
printf "%-15s %-20s %-15s\n" "----" "----" "--"
printf "%-15s %-20s %-15s\n" "Edge" "${CHOMS_EDGE_NODE}" "${CHOMS_EDGE_IP}"
printf "%-15s %-20s %-15s\n" "Application" "${CHOMS_APPLICATION_NODE}" "${CHOMS_APPLICATION_IP}"
printf "%-15s %-20s %-15s\n" "Storage" "${CHOMS_STORAGE_NODE}" "${CHOMS_STORAGE_IP}"
