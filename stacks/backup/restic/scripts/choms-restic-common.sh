#!/usr/bin/env bash
set -euo pipefail
set +x
export RESTIC_PASSWORD_FILE=/etc/choms-backup/restic-password
METRIC_FILE=/var/lib/node_exporter/textfile_collector/choms_restic_backup.prom
LOCK_FILE=/run/lock/choms-restic-backup.lock
MAX_LOGICAL_BYTES=$((25 * 1024 * 1024 * 1024))
RESTIC_OPTIONS=()
if test -n "${CHOMS_RESTIC_SFTP_KEY:-}"; then
  test -f "$CHOMS_RESTIC_SFTP_KEY"
  RESTIC_OPTIONS=(
    -o
    "sftp.command=ssh -i $CHOMS_RESTIC_SFTP_KEY -o BatchMode=yes -o NumberOfPasswordPrompts=0 -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no -o IdentitiesOnly=yes -o IdentityAgent=none -o StrictHostKeyChecking=yes -o UserKnownHostsFile=/root/.ssh/choms-restic-known_hosts choms-restic@192.168.1.134 -s sftp"
  )
fi
test "$(id -u)" -eq 0
test "$(stat -Lc '%U:%G:%a' "$RESTIC_PASSWORD_FILE")" = root:root:600
exec 9>"$LOCK_FILE"
flock -n 9 || { echo 'ERROR: local backup already active' >&2; exit 75; }
run_restic() { command restic "${RESTIC_OPTIONS[@]}" "$@"; }
publish_metric() {
  status=$1 duration=$2 bytes=$3 timestamp=$4
  tmp="${METRIC_FILE}.tmp.$$"
  install -d -m 0755 "${METRIC_FILE%/*}"
  umask 022
  printf 'choms_restic_backup_success %s\nchoms_restic_backup_duration_seconds %s\nchoms_restic_backup_logical_bytes %s\nchoms_restic_backup_last_success_unixtime %s\n' "$status" "$duration" "$bytes" "$timestamp" >"$tmp"
  chmod 0644 "$tmp"
  mv "$tmp" "$METRIC_FILE"
}
require_below_limit() {
  logical_bytes=$1
  test "$logical_bytes" -le "$MAX_LOGICAL_BYTES" || {
    echo "ERROR: logical scope exceeds the authorized 25 GiB limit" >&2
    return 1
  }
}
