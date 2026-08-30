#!/usr/bin/env bash
# shellcheck disable=SC1091
export CHOMS_RESTIC_SFTP_KEY=/root/.ssh/choms-restic-node02
source /usr/local/lib/choms-restic-common.sh
export RESTIC_REPOSITORY='sftp:choms-restic@192.168.1.134:/choms-platforms-restic'
rc=0; start=$(date +%s); trap 'rc=$?; [ "$rc" -eq 0 ] || publish_metric 0 "$(( $(date +%s)-start ))" 0 0; exit "$rc"' EXIT INT TERM
require_below_limit 1117507584
run_restic --retry-lock 20m backup --host choms-node-02 --tag node-02 --tag type-jellyfin --exclude cache --exclude '*/transcodes/**' -- /data/docker/jellyfin-node02/config
publish_metric 1 "$(( $(date +%s)-start ))" 1117507584 "$(date +%s)"; trap - EXIT
