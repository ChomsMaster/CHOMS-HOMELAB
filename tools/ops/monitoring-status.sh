#!/bin/bash
set -euo pipefail

echo "=============================================="
echo " CHOMS-HOMELAB Monitoring Status"
echo "=============================================="
echo

printf "%-18s %-12s %-30s\n" "Service" "Status" "URL"
printf "%-18s %-12s %-30s\n" "-------" "------" "---"

check_container() {
    local name="$1"
    local url="$2"

    if docker ps --format '{{.Names}}' | grep -qx "$name"; then
        status="RUNNING"
    else
        status="STOPPED"
    fi

    printf "%-18s %-12s %-30s\n" "$name" "$status" "$url"
}

check_container "choms-grafana" "http://192.168.1.138:3000"
check_container "choms-prometheus" "http://192.168.1.138:9090"
check_container "choms-node-exporter" "http://192.168.1.138:9100"
check_container "choms-cadvisor" "http://192.168.1.138:8082"
check_container "choms-uptime-kuma" "http://192.168.1.138:3001"
check_container "choms-scrutiny" "http://192.168.1.138:8083"

echo
echo "Compose project:"
docker compose -f /data/projects/choms-homelab/docker/compose.yml ps \
  choms-grafana choms-prometheus choms-node-exporter choms-cadvisor choms-uptime-kuma 2>/dev/null || true
