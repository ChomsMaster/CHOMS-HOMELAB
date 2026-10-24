#!/usr/bin/env bash
# Public-recipient-only offline encryption. No capture or restore operations.
set +x
set -euo pipefail
umask 077
ulimit -c 0
child=''
# Trap callbacks are asynchronous; exercised by the synthetic signal tests.
# shellcheck disable=SC2317
cleanup() {
  local code=$?
  trap - EXIT INT TERM HUP
  if [[ -n $child ]]; then
    kill -TERM "$child" 2>/dev/null || true
    wait "$child" 2>/dev/null || true
  fi
  exit "$code"
}
# shellcheck disable=SC2317
forward() {
  local sig=$1 code=$2
  trap '' INT TERM HUP
  if [[ -n $child ]]; then
    kill -s "$sig" "$child" 2>/dev/null || true
    wait "$child" 2>/dev/null || true
    child=''
  fi
  exit "$code"
}
trap cleanup EXIT
trap 'forward INT 130' INT
trap 'forward TERM 143' TERM
trap 'forward HUP 129' HUP
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
# Isolated mode ignores Python environment overrides and user site configuration.
python3 -I -B "$script_dir/recovery_kit.py" export "$@" &
child=$!
status=0
wait "$child" || status=$?
child=''
exit "$status"
