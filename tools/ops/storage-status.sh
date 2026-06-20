#!/bin/bash

set -euo pipefail

bar() {
    local used="$1"
    local width=30
    local filled=$(( used * width / 100 ))
    local empty=$(( width - filled ))

    printf "["
    printf "%0.s█" $(seq 1 "$filled")
    printf "%0.s░" $(seq 1 "$empty")
    printf "]"
}

echo "=============================================="
echo " CHOMS-HOMELAB Storage Status"
echo "=============================================="
echo

printf "%-22s %-10s %-10s %-10s %-6s %s\n" "Mount" "Size" "Used" "Avail" "Use%" "Bar"
printf "%-22s %-10s %-10s %-10s %-6s %s\n" "-----" "----" "----" "-----" "----" "---"

df -h | awk 'NR>1 && ($6=="/" || $6=="/data" || $6 ~ "^/media" || $6 ~ "^/archive") {print $6, $2, $3, $4, $5}' | while read -r mount size used avail pct; do
    num="${pct%\%}"
    printf "%-22s %-10s %-10s %-10s %-6s " "$mount" "$size" "$used" "$avail" "$pct"
    bar "$num"
    echo
done

echo
echo "===== DISKS / PARTITIONS ====="
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT

echo
echo "===== KEY PATHS SIZE ====="
for path in /data /media/ssd-media; do
    if [ -d "$path" ]; then
        echo -n "$path: "
        du -sh "$path" 2>/dev/null || sudo du -sh "$path"
    else
        echo "$path: not found"
    fi
done
