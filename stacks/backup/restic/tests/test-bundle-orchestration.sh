#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ORCHESTRATOR=$ROOT/deploy-encrypted-recovery.sh
KEY_INSTALLER=$ROOT/scripts/choms-restic-key-install.sh
NODE03=$ROOT/scripts/choms-restic-deploy-node03.sh
COMMON=$ROOT/scripts/choms-restic-deploy-bundle-common.sh

for bundle in choms-restic-deploy-node01.sh choms-restic-deploy-node02.sh choms-restic-deploy-node03.sh; do
  test -x "$ROOT/scripts/$bundle"
done

deploy_block=$(sed -n '/^  deploy)/,/^  resume-initialize)/p' "$ORCHESTRATOR")
test "$(grep -c 'run_staged_bundle choms-node-01' <<<"$deploy_block")" -eq 2
test "$(grep -c 'run_staged_bundle choms-node-02' <<<"$deploy_block")" -eq 2
test "$(grep -c 'run_staged_bundle choms-node-03' <<<"$deploy_block")" -eq 2
if grep -Eq 'remote_sudo|sudo[[:space:]]+-S|SUDO_ASKPASS=' "$ORCHESTRATOR"; then exit 1; fi
grep -Fq 'sudo_authentication=6 restic_password_entries=6 custody_confirmation_attempts=9 initialization_confirmation_attempts=3 total_maximum=24 normal_first_attempt=16' "$ORCHESTRATOR"

grep -Fq "printf 'RESTIC PASSWORD FOR %s" "$KEY_INSTALLER"
test "$(grep -c 'read -r -s' "$KEY_INSTALLER")" -eq 2
grep -Fq 'TYPE STORED' "$KEY_INSTALLER"
grep -Fq "bundle_confirm_literal 'INITIALIZE choms-platforms-restic'" "$NODE03"
grep -Fq 'bundle_clear_before_initialize' "$NODE03"
grep -Fq 'password_input=finished' "$NODE03"

if grep -Eq 'scp[^[:cntrl:]]*/root/\.ssh/choms-restic-node0[12]([^.]|$)' "$ORCHESTRATOR"; then exit 1; fi
grep -Fq 'private_key_transferred=false' "$ORCHESTRATOR"
grep -Fq "systemctl start --no-block \"\$FINALIZER\"" "$ROOT/scripts/choms-restic-deploy-node01.sh"
grep -Fq "systemctl start --no-block \"\$FINALIZER\"" "$ROOT/scripts/choms-restic-deploy-node02.sh"

next_phase() {
  local origins_prepared=$1 repository_initialized=$2 node01_backup=$3 node02_backup=$4 global_validated=$5 timers_enabled=$6
  if test "$origins_prepared" -eq 0; then echo prepare-origins
  elif test "$repository_initialized" -eq 0; then echo prepare-node03-and-initialize
  elif test "$node01_backup" -eq 0; then echo execute-node01
  elif test "$node02_backup" -eq 0; then echo execute-node02
  elif test "$global_validated" -eq 0; then echo execute-node03-and-validate
  elif test "$timers_enabled" -eq 0; then echo release-finalizer-gates
  else echo complete
  fi
}

test "$(next_phase 0 0 0 0 0 0)" = prepare-origins
test "$(next_phase 1 0 0 0 0 0)" = prepare-node03-and-initialize
test "$(next_phase 1 1 0 0 0 0)" = execute-node01
test "$(next_phase 1 1 1 0 0 0)" = execute-node02
test "$(next_phase 1 1 1 1 0 0)" = execute-node03-and-validate
test "$(next_phase 1 1 1 1 1 0)" = release-finalizer-gates
test "$(next_phase 1 1 1 1 1 1)" = complete

confirmation_output=$(printf 'STORED\n' | script -qec "bash -c 'source \"$COMMON\"; bundle_confirm_literal STORED \"confirm: \"'" /dev/null)
test -n "$confirmation_output"
confirmation_output=$(printf 'WRONG\nSTORED\n' | script -qec "bash -c 'source \"$COMMON\"; bundle_confirm_literal STORED \"confirm: \"'" /dev/null)
grep -Fq 'confirmation_mismatch retry=1/3' <<<"$confirmation_output"
confirmation_output=$(printf 'STORED \nSTORED\n' | script -qec "bash -c 'source \"$COMMON\"; bundle_confirm_literal STORED \"confirm: \"'" /dev/null)
grep -Fq 'confirmation_mismatch retry=1/3' <<<"$confirmation_output"
three_failures=$(mktemp)
trap 'rm -f -- "$three_failures"' EXIT HUP INT TERM
if printf 'WRONG\nWRONG\nWRONG\n' | script -qec "bash -c 'source \"$COMMON\"; bundle_confirm_literal STORED \"confirm: \"'" "$three_failures" >/dev/null; then
  echo 'ERROR: three incorrect confirmations were accepted' >&2
  exit 1
fi
grep -Fq 'confirmation_mismatch retry=3/3' "$three_failures"

resume_block=$(sed -n '/^  resume-initialize)/,/^  validate)/p' "$ORCHESTRATOR")
test "$(grep -c 'run_staged_bundle choms-node-03' <<<"$resume_block")" -eq 1
test "$(grep -c 'run_staged_bundle choms-node-01' <<<"$resume_block")" -eq 1
test "$(grep -c 'run_staged_bundle choms-node-02' <<<"$resume_block")" -eq 1
grep -Fq 'total_maximum=21' <<<"$resume_block"

echo 'bundle_orchestration_tests=passed sudo_sessions_per_node=2 prompt_success=passed prompt_retry=passed prompt_three_failures=passed resume_initialization=passed private_key_transfer=absent'
