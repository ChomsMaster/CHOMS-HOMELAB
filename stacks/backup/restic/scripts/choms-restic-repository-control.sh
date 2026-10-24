#!/usr/bin/env bash
set -euo pipefail
set +x
export RESTIC_REPOSITORY=/mnt/choms-local/backups/choms-platforms-restic
export RESTIC_PASSWORD_FILE=/etc/choms-backup/restic-password
REPOSITORY_MARKER=$RESTIC_REPOSITORY/.choms-platforms-restic
test "$(id -u)" -eq 0
test "$(stat -Lc '%U:%G:%a' "$RESTIC_PASSWORD_FILE")" = root:root:600
case "${1:-}" in
  init)
    test ! -e "$RESTIC_REPOSITORY/config"
    if test ! -e "$REPOSITORY_MARKER"; then
      test -z "$(find "$RESTIC_REPOSITORY" -mindepth 1 -maxdepth 1 -print -quit)"
      install -o choms-restic -g choms-restic -m 0600 /dev/null "$REPOSITORY_MARKER"
    fi
    restic init
    chown -R choms-restic:choms-restic "$RESTIC_REPOSITORY"
    ;;
  check) restic check ;;
  snapshots) restic snapshots --compact ;;
  *) echo 'usage: choms-restic-repository-control.sh {init|check|snapshots}' >&2; exit 2 ;;
esac
