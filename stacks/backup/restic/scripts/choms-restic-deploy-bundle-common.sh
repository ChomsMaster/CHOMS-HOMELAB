#!/usr/bin/env bash
set -euo pipefail
set +x

bundle_fail() { echo "ERROR: $*" >&2; exit 1; }
bundle_phase() { printf '\n-- %s --\n' "$*"; }

bundle_confirm_literal() {
  local expected=$1 prompt=$2 attempt answer
  for attempt in 1 2 3; do
    IFS= read -r -p "$prompt" answer </dev/tty
    if test "$answer" = "$expected"; then unset answer; return 0; fi
    answer=; unset answer
    echo "confirmation_mismatch retry=$attempt/3" >/dev/tty
  done
  return 1
}

bundle_require_root() {
  local mode=${1:-}
  test "$(id -u)" -eq 0 || bundle_fail 'bundle must run through sudo'
  if test "$mode" = finalize; then return 0; fi
  test "${SUDO_USER:-}" = chomsmaster || bundle_fail 'bundle sudo user must be chomsmaster'
  if ! test -t 0 || ! test -t 1; then bundle_fail 'bundle requires one visible interactive TTY'; fi
}

bundle_install() {
  local source=$1 destination=$2 mode=$3 owner=${4:-root} group=${5:-root}
  if ! test -f "$source" || test -L "$source"; then bundle_fail "invalid payload: ${source##*/}"; fi
  install -D -o "$owner" -g "$group" -m "$mode" "$source" "$destination"
}

bundle_assert_stat() {
  local path=$1 expected=$2
  test "$(stat -Lc '%U:%G:%a' "$path")" = "$expected" ||
    bundle_fail "unexpected owner or mode: $path"
}

bundle_install_password() {
  local node=$1
  /usr/local/sbin/choms-restic-key-install.sh "$node"
  bundle_assert_stat /etc/choms-backup/restic-password root:root:600
}

bundle_password_install_evidence() {
  local marker="/var/lib/choms-restic-deploy/password-$1.ready"
  bundle_password_metadata_valid && test -f "$marker" && test ! -L "$marker" &&
    test "$(stat -Lc '%U:%G:%a:%s' "$marker")" = root:root:600:0
}

bundle_password_metadata_valid() {
  test -f /etc/choms-backup/restic-password &&
    test ! -L /etc/choms-backup/restic-password &&
    test "$(stat -Lc '%U:%G:%a' /etc/choms-backup/restic-password)" = root:root:600 &&
    test -s /etc/choms-backup/restic-password
}

bundle_clear_before_initialize() {
  unset REPLY confirmation first second stored_answer initialize_answer || true
  printf '\033[2J\033[H' >/dev/tty
  printf '%s\n' 'RESTIC PASSWORD INPUT FINISHED; INITIALIZATION IS A SEPARATE GATE.' >/dev/tty
}

bundle_wait_for_validation_marker() {
  local marker=$1 attempts=${2:-720}
  local attempt
  for ((attempt = 0; attempt < attempts; attempt++)); do
    if test -f "$marker" && test ! -L "$marker"; then
      test "$(stat -Lc '%U:%G:%a' "$marker")" = chomsmaster:chomsmaster:600 ||
        bundle_fail 'validation marker has unexpected metadata'
      return 0
    fi
    sleep 5
  done
  bundle_fail 'timed out waiting for the post-validation marker'
}
