#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
REMOTE_CHECK=$ROOT/scripts/choms-restic-remote-check.sh

interpret_negative_probe() {
  local command_status=$1
  if test "$command_status" -eq 0; then
    echo unexpectedly_allowed
    return 1
  fi
  echo denied_as_expected
}

interpret_transport_probe() {
  local node=$1 command_status=$2
  if test "$command_status" -eq 0; then
    echo "transport_probe=$node result=passed"
    return 0
  fi
  echo "transport_probe=$node result=failed" >&2
  return 1
}

test "$(interpret_negative_probe 255)" = denied_as_expected
if interpret_negative_probe 0 >/dev/null; then
  echo 'ERROR: successful forbidden command was accepted by the test harness' >&2
  exit 1
fi

test "$(interpret_transport_probe node-01 0)" = 'transport_probe=node-01 result=passed'
transport_failure=$(mktemp)
key_test_dir=$(mktemp -d)
trap 'rm -f -- "$transport_failure"; rm -rf -- "$key_test_dir"' EXIT HUP INT TERM
if interpret_transport_probe node-02 255 2>"$transport_failure"; then
  echo 'ERROR: failed SFTP transport was accepted by the test harness' >&2
  exit 1
fi
test "$(<"$transport_failure")" = 'transport_probe=node-02 result=failed'

ssh-keygen -q -t ed25519 -N '' -C node-01-test -f "$key_test_dir/node01"
ssh-keygen -q -t ed25519 -N '' -C node-02-test -f "$key_test_dir/node02"
printf 'from="192.168.1.138",restrict,command="internal-sftp -d /choms-platforms-restic" %s\n' "$(<"$key_test_dir/node01.pub")" >"$key_test_dir/authorized_keys"
printf 'from="192.168.1.172",restrict,command="internal-sftp -d /choms-platforms-restic" %s\n' "$(<"$key_test_dir/node02.pub")" >>"$key_test_dir/authorized_keys"
"$REMOTE_CHECK" validate-authorized-keys "$key_test_dir/authorized_keys" >/dev/null
sed -n '1p' "$key_test_dir/authorized_keys" >"$key_test_dir/invalid-authorized_keys"
if "$REMOTE_CHECK" validate-authorized-keys "$key_test_dir/invalid-authorized_keys" >/dev/null 2>&1; then
  echo 'ERROR: incomplete authorized_keys was accepted by the validator' >&2
  exit 1
fi

echo 'probe_handling_tests=passed transport_success=passed transport_failure=reported negative_denial=success negative_allow=failure authorized_keys=validated'
