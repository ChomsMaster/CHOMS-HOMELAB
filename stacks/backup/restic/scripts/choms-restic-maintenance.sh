#!/usr/bin/env bash
# shellcheck disable=SC1091
source /usr/local/lib/choms-restic-common.sh
export RESTIC_REPOSITORY=/mnt/choms-local/backups/choms-platforms-restic
test -z "$(run_restic list locks --no-lock 2>/dev/null)" || { echo 'ERROR: repository lock active; forget skipped' >&2; exit 75; }
for group in 'choms-node-01 node-01 type-k3s' 'choms-node-01 node-01 type-secrets' 'choms-node-01 node-01 type-platform' 'choms-node-01 node-01 type-nextcloud' 'choms-node-02 node-02 type-jellyfin' 'choms-node-03 node-03 type-qbittorrent'; do
  read -r host host_tag type_tag <<<"$group"
  run_restic --retry-lock 20m forget --dry-run --host "$host" --tag "$host_tag" --tag "$type_tag" --group-by host,tags --keep-daily 7 --keep-weekly 4 --keep-monthly 6
done
echo 'Dry-run only: real forget remains disabled until selection is approved.'
