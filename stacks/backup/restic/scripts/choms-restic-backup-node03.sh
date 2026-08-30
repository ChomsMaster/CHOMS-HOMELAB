#!/usr/bin/env bash
# shellcheck disable=SC1091
source /usr/local/lib/choms-restic-common.sh
export RESTIC_REPOSITORY=/mnt/choms-local/backups/choms-platforms-restic
rc=0; start=$(date +%s); trap 'rc=$?; [ "$rc" -eq 0 ] || publish_metric 0 "$(( $(date +%s)-start ))" 0 0; exit "$rc"' EXIT INT TERM
require_below_limit 8744960
run_restic --retry-lock 20m backup --host choms-node-03 --tag node-03 --tag type-qbittorrent --exclude '*/downloads/**' -- /data/docker/qbittorrent/config
chown -R choms-restic:choms-restic "$RESTIC_REPOSITORY"
publish_metric 1 "$(( $(date +%s)-start ))" 8744960 "$(date +%s)"; trap - EXIT
