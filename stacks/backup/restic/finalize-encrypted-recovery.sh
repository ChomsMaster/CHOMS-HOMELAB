#!/usr/bin/env bash
set -euo pipefail
set +x
umask 077

fail() { echo "ERROR: $*" >&2; exit 1; }
phase() { printf '\n== %s ==\n' "$*"; }

SCRIPT_SOURCE=${BASH_SOURCE[0]:-}
if test -n "$SCRIPT_SOURCE"; then
  SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$SCRIPT_SOURCE")" && pwd)
else
  SCRIPT_DIR=${CHOMS_FINALIZER_BASE_DIR:-}
fi
LOCAL_SCOPE_VALIDATOR=${SCRIPT_DIR:+$SCRIPT_DIR/scripts/choms-restic-validate-snapshot-scope.py}
KNOWN_HOSTS=${HOME}/.ssh/known_hosts
SSH_OPTIONS=(
  -F /dev/null
  -o ConnectTimeout=10
  -o ConnectionAttempts=1
  -o ServerAliveInterval=15
  -o ServerAliveCountMax=2
  -o BatchMode=yes
  -o ForwardAgent=no
  -o IdentityAgent=none
  -o IdentitiesOnly=yes
  -o StrictHostKeyChecking=yes
  -o UserKnownHostsFile="$KNOWN_HOSTS"
)
REPOSITORY=/mnt/choms-local/backups/choms-platforms-restic
PASSWORD_FILE=/etc/choms-backup/restic-password
METRIC_FILE=/var/lib/node_exporter/textfile_collector/choms_restic_backup.prom
STATE_DIR=/var/lib/choms-restic-deploy
CHECK_STATE=$STATE_DIR/final-restic-check.state
REPORT=$STATE_DIR/final-validation.env
MAX_LOGICAL_BYTES=$((25 * 1024 * 1024 * 1024))
ACTIVATION_GUARD_SECONDS=120
TTY_DEVICE=${CHOMS_FINALIZER_TTY:-/dev/tty}
REPOSITORY_WORK=''
REPOSITORY_WORK_OWNER_UID=''
REMOTE_FILES=()

usage() {
  echo 'usage: finalize-encrypted-recovery.sh {finalize|validate}' >&2
  exit 2
}

timer_spec() {
  case "$1" in
    choms-restic-backup-node01.timer)
      printf '%s\n' '*-*-* 05:00:00 Europe/Madrid' 'choms-restic-backup.service'
      ;;
    choms-restic-backup-node02.timer)
      printf '%s\n' '*-*-* 05:30:00 Europe/Madrid' 'choms-restic-backup.service'
      ;;
    choms-restic-backup-node03.timer)
      printf '%s\n' '*-*-* 06:00:00 Europe/Madrid' 'choms-restic-backup.service'
      ;;
    choms-restic-maintenance.timer)
      printf '%s\n' '*-*-* 06:30:00 Europe/Madrid' 'choms-restic-maintenance.service'
      ;;
    *) fail "unexpected timer: $1" ;;
  esac
}

timer_calendar_is_declared() {
  local timer=$1 expected=$2 unit_text found=0 line value
  unit_text=$(systemctl cat "$timer") || fail "unable to read $timer"
  while IFS= read -r line; do
    case "$line" in
      OnCalendar=*)
        value=${line#OnCalendar=}
        test "$value" = "$expected" || fail "$timer has an unexpected calendar"
        found=$((found + 1))
        ;;
    esac
  done <<<"$unit_text"
  test "$found" -eq 1 || fail "$timer must declare exactly one calendar"
  grep -Fxq 'Persistent=true' <<<"$unit_text" || fail "$timer is not persistent"
}

calendar_next_epoch() {
  local calendar=$1 baseline=$2 output next_text
  output=$(systemd-analyze calendar --iterations=1 --base-time="@$baseline" "$calendar") ||
    fail 'unable to calculate timer calendar'
  next_text=$(sed -n -E 's/^[[:space:]]*Next elapse: //p' <<<"$output")
  test "$(wc -l <<<"$next_text")" -eq 1 || fail 'unable to identify next calendar elapse'
  date -d "$next_text" +%s
}

timer_precheck() {
  local timer=$1 calendar service active fragment stamp baseline now next_epoch
  local -a spec
  mapfile -t spec < <(timer_spec "$timer")
  calendar=${spec[0]}; service=${spec[1]}
  systemctl is-enabled --quiet "$timer" || fail "$timer is not enabled"
  timer_calendar_is_declared "$timer" "$calendar"
  active=$(systemctl is-active "$timer" 2>/dev/null || true)
  if test "$active" = active; then
    echo "timer_precheck=$timer result=already_active"
    return 0
  fi
  test "$active" = inactive || fail "$timer has unexpected active state: $active"
  if systemctl is-active --quiet "$service"; then
    fail "$service is active; timer activation stopped"
  fi
  fragment=$(systemctl show "$timer" -p FragmentPath --value)
  test -f "$fragment" || fail "$timer fragment is unavailable"
  stamp=/var/lib/systemd/timers/stamp-$timer
  if test -e "$stamp"; then
    baseline=$(stat -Lc '%Y' "$stamp") || fail "unable to inspect $timer persistent stamp"
    baseline_source=persistent_stamp
  else
    baseline=$(stat -Lc '%Y' "$fragment") || fail "unable to inspect $timer fragment"
    baseline_source=unit_install_time
  fi
  now=$(date +%s)
  next_epoch=$(calendar_next_epoch "$calendar" "$baseline")
  if test "$next_epoch" -le "$now"; then
    echo "timer_catchup_risk=$timer cause=scheduled_elapse_after_${baseline_source} action=stopped_before_activation" >&2
    return 75
  fi
  if test $((next_epoch - now)) -le "$ACTIVATION_GUARD_SECONDS"; then
    echo "timer_catchup_risk=$timer cause=calendar_elapse_within_activation_guard action=stopped_before_activation" >&2
    return 75
  fi
  printf 'timer_precheck=%s result=safe next_epoch=%s baseline_source=%s\n' \
    "$timer" "$next_epoch" "$baseline_source"
}

validate_metric() {
  local now mtime age
  test -f "$METRIC_FILE" && test ! -L "$METRIC_FILE" || fail 'Restic metric is not a regular file'
  test "$(stat -Lc '%U:%G:%a' "$METRIC_FILE")" = root:root:644 || fail 'Restic metric permissions are invalid'
  awk '
    $1 == "choms_restic_backup_success" && $2 == 1 { success++ }
    $1 == "choms_restic_backup_duration_seconds" && $2 ~ /^[0-9]+([.][0-9]+)?$/ { duration++ }
    $1 == "choms_restic_backup_logical_bytes" && $2 ~ /^[0-9]+$/ { logical++ }
    $1 == "choms_restic_backup_last_success_unixtime" && $2 ~ /^[0-9]+$/ && $2 > 0 { fresh++ }
    END { exit !(success == 1 && duration == 1 && logical == 1 && fresh == 1 && NR == 4) }
  ' "$METRIC_FILE" || fail 'Restic metric content is invalid'
  now=$(date +%s); mtime=$(stat -Lc '%Y' "$METRIC_FILE"); age=$((now - mtime))
  test "$age" -ge 0 && test "$age" -le 86400 || fail 'Restic metric is stale'
  echo "metric=present result=passed age_seconds=$age"
}

run_restic() {
  RESTIC_REPOSITORY=$REPOSITORY RESTIC_PASSWORD_FILE=$PASSWORD_FILE restic "$@"
}

check_once() {
  local state temporary
  install -d -o root -g root -m 0755 "$STATE_DIR"
  if test -e "$CHECK_STATE"; then
    test -f "$CHECK_STATE" && test ! -L "$CHECK_STATE" || fail 'invalid Restic check state'
    test "$(stat -Lc '%U:%G:%a' "$CHECK_STATE")" = root:root:600 || fail 'invalid Restic check state permissions'
    state=$(<"$CHECK_STATE")
    test "$state" = passed || fail 'a previous final Restic check did not complete; refusing to repeat it'
    echo 'restic_check=passed execution=reused'
    return 0
  fi
  temporary=$(mktemp "$STATE_DIR/.final-restic-check.XXXXXX")
  chmod 0600 "$temporary"
  printf 'started\n' >"$temporary"
  mv -f -- "$temporary" "$CHECK_STATE"
  temporary=$(mktemp /run/choms-restic-final-check.XXXXXX)
  chmod 0600 "$temporary"
  if ! run_restic check >"$temporary" 2>&1; then
    rm -f -- "$temporary"
    fail 'restic check failed; it will not be repeated automatically'
  fi
  rm -f -- "$temporary"
  temporary=$(mktemp "$STATE_DIR/.final-restic-check.XXXXXX")
  chmod 0600 "$temporary"
  printf 'passed\n' >"$temporary"
  mv -f -- "$temporary" "$CHECK_STATE"
  echo 'restic_check=passed execution=performed_once'
}

cleanup_repository_work() {
  local target=${REPOSITORY_WORK:-} owner_uid=${REPOSITORY_WORK_OWNER_UID:-}
  test -n "$target" || return 0
  case "$target" in
    /tmp/choms-restic-finalize.*) ;;
    *) echo 'ERROR: unsafe repository-validation cleanup target' >&2; return 1 ;;
  esac
  test -n "$owner_uid" || { echo 'ERROR: repository-validation cleanup owner is unset' >&2; return 1; }
  if test ! -e "$target"; then
    REPOSITORY_WORK=''; REPOSITORY_WORK_OWNER_UID=''
    return 0
  fi
  test -d "$target" && test ! -L "$target" || {
    echo 'ERROR: repository-validation cleanup target is not a directory' >&2
    return 1
  }
  test "$(stat -Lc '%u' "$target")" = "$owner_uid" || {
    echo 'ERROR: repository-validation cleanup ownership mismatch' >&2
    return 1
  }
  rm -rf -- "$target"
  REPOSITORY_WORK=''; REPOSITORY_WORK_OWNER_UID=''
}

collect_repository_validation() {
  local work snapshots selected restore_stats raw_stats logical stored report_tmp scope_validator
  local snapshot_id hostname host_tag type_tag logical_name scope_listing
  scope_validator=$1
  test -f "$scope_validator" && test ! -L "$scope_validator" || fail 'scope validator is unavailable'
  REPOSITORY_WORK=$(mktemp -d /tmp/choms-restic-finalize.XXXXXX)
  REPOSITORY_WORK_OWNER_UID=$(id -u)
  chmod 0700 "$REPOSITORY_WORK"
  trap cleanup_repository_work EXIT HUP INT TERM
  work=$REPOSITORY_WORK
  snapshots=$work/snapshots.json; selected=$work/selected
  restore_stats=$work/restore-stats.json; raw_stats=$work/raw-stats.json
  if ! run_restic snapshots --json >"$snapshots" 2>"$work/restic.stderr"; then
    echo 'scope_validation=error category=technical' >&2
    return 1
  fi
  chmod 0600 "$snapshots"
  python3 - "$snapshots" "$selected" <<'PY'
import json
import sys

expected = {
    ("choms-node-01", "node-01", "type-k3s"): "-",
    ("choms-node-01", "node-01", "type-secrets"): "recovery-secrets.json",
    ("choms-node-01", "node-01", "type-platform"): "-",
    ("choms-node-01", "node-01", "type-nextcloud"): "-",
    ("choms-node-02", "node-02", "type-jellyfin"): "-",
    ("choms-node-03", "node-03", "type-qbittorrent"): "-",
}
try:
    with open(sys.argv[1], encoding="utf-8") as source:
        snapshots = json.load(source)
    if not isinstance(snapshots, list):
        raise ValueError("snapshot list is malformed")
except (OSError, ValueError, json.JSONDecodeError):
    print("scope_validation=error category=technical", file=sys.stderr)
    raise SystemExit(30)
matches = {key: [] for key in expected}
for snapshot in snapshots:
    if not isinstance(snapshot, dict):
        print("scope_validation=error category=technical", file=sys.stderr)
        raise SystemExit(30)
    tags = set(snapshot.get("tags") or [])
    host = snapshot.get("hostname")
    for key in expected:
        expected_host, host_tag, type_tag = key
        if host == expected_host and {host_tag, type_tag}.issubset(tags):
            matches[key].append(snapshot.get("id"))
if any(len(ids) < 1 or any(not value for value in ids) for ids in matches.values()):
    print("scope_validation=failed category=snapshot_set", file=sys.stderr)
    raise SystemExit(20)
with open(sys.argv[2], "w", encoding="ascii") as destination:
    for key, ids in matches.items():
        destination.write(f"{ids[-1]} {key[0]} {key[1]} {key[2]} {expected[key]}\n")
PY
  chmod 0600 "$selected"
  scope_listing=$work/scope.jsonl
  while read -r snapshot_id hostname host_tag type_tag logical_name; do
    if ! run_restic ls --json "$snapshot_id" >"$scope_listing" 2>"$work/restic.stderr"; then
      echo 'scope_validation=error category=technical' >&2
      return 1
    fi
    if ! python3 "$scope_validator" "$hostname" "$host_tag" "$type_tag" "$logical_name" <"$scope_listing"; then
      return 1
    fi
    : >"$scope_listing"
  done <"$selected"
  if ! run_restic stats --mode restore-size --json >"$restore_stats" 2>"$work/restic.stderr" ||
     ! run_restic stats --mode raw-data --json >"$raw_stats" 2>"$work/restic.stderr"; then
    echo 'repository_stats=error category=technical' >&2
    return 1
  fi
  read -r logical stored < <(python3 - "$restore_stats" "$raw_stats" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as source:
    logical = json.load(source).get("total_size")
with open(sys.argv[2], encoding="utf-8") as source:
    stored = json.load(source).get("total_size")
if not isinstance(logical, int) or logical < 0 or not isinstance(stored, int) or stored < 0:
    raise SystemExit("repository statistics are unavailable")
print(logical, stored)
PY
  )
  test "$logical" -le "$MAX_LOGICAL_BYTES" || fail 'aggregate logical size exceeds 25 GiB'
  report_tmp=$(mktemp "$STATE_DIR/.final-validation.XXXXXX")
  chmod 0644 "$report_tmp"
  {
    echo 'validation_version=1'
    echo 'restic_check=passed'
    echo 'scope_validation=passed'
    echo 'snapshots_hostname_tags=passed'
    echo 'snapshot_choms_node_01_node_01_type_k3s=present'
    echo 'snapshot_choms_node_01_node_01_type_secrets=present'
    echo 'snapshot_choms_node_01_node_01_type_platform=present'
    echo 'snapshot_choms_node_01_node_01_type_nextcloud=present'
    echo 'snapshot_choms_node_02_node_02_type_jellyfin=present'
    echo 'snapshot_choms_node_03_node_03_type_qbittorrent=present'
    echo 'snapshot_node03=present'
    printf 'logical_bytes=%s\nstored_bytes=%s\nlimit_bytes=%s\n' "$logical" "$stored" "$MAX_LOGICAL_BYTES"
    echo 'limit_result=passed'
    echo 'exclusion_nextcloud_data=passed'
    echo 'exclusion_multimedia=passed'
    echo 'exclusion_downloads=passed'
    echo 'exclusion_colegio=passed'
    echo 'exclusion_personal_backups=passed'
    echo 'exclusion_prometheus_tsdb=passed'
    echo 'exclusion_loki=passed'
    printf 'validated_at_unixtime=%s\n' "$(date +%s)"
  } >"$report_tmp"
  mv -f -- "$report_tmp" "$REPORT"
  trap - EXIT HUP INT TERM
  cleanup_repository_work
}

report_is_valid() {
  test -f "$REPORT" && test ! -L "$REPORT" || return 1
  test "$(stat -Lc '%U:%G:%a' "$REPORT")" = root:root:644 || return 1
  for expected in \
    validation_version=1 restic_check=passed scope_validation=passed snapshots_hostname_tags=passed snapshot_node03=present \
    snapshot_choms_node_01_node_01_type_k3s=present \
    snapshot_choms_node_01_node_01_type_secrets=present \
    snapshot_choms_node_01_node_01_type_platform=present \
    snapshot_choms_node_01_node_01_type_nextcloud=present \
    snapshot_choms_node_02_node_02_type_jellyfin=present \
    snapshot_choms_node_03_node_03_type_qbittorrent=present \
    limit_result=passed exclusion_nextcloud_data=passed exclusion_multimedia=passed \
    exclusion_downloads=passed exclusion_colegio=passed exclusion_personal_backups=passed \
    exclusion_prometheus_tsdb=passed exclusion_loki=passed; do
    grep -Fxq "$expected" "$REPORT" || return 1
  done
  awk -F= -v limit="$MAX_LOGICAL_BYTES" '
    $1 == "logical_bytes" && $2 ~ /^[0-9]+$/ && $2 <= limit { logical++ }
    $1 == "stored_bytes" && $2 ~ /^[0-9]+$/ { stored++ }
    END { exit !(logical == 1 && stored == 1) }
  ' "$REPORT"
}

activate_timer() {
  local timer=$1 service before_invocation after_invocation state next
  local -a spec
  mapfile -t spec < <(timer_spec "$timer"); service=${spec[1]}
  if systemctl is-active --quiet "$timer"; then
    state=already_active
  else
    timer_precheck "$timer"
    before_invocation=$(systemctl show "$service" -p InvocationID --value)
    systemctl start "$timer"
    after_invocation=$(systemctl show "$service" -p InvocationID --value)
    test "$before_invocation" = "$after_invocation" || fail "$service was unexpectedly invoked"
    state=activated
  fi
  systemctl is-enabled --quiet "$timer" || fail "$timer is not enabled after activation"
  systemctl is-active --quiet "$timer" || fail "$timer is not active after activation"
  test "$(systemctl show "$timer" -p SubState --value)" = waiting || fail "$timer is not waiting"
  next=$(systemctl show "$timer" -p NextElapseUSecRealtime --value)
  test -n "$next" && test "$next" != n/a || fail "$timer has no next execution"
  printf 'timer=%s result=%s enabled=true active=true substate=waiting next=%s\n' "$timer" "$state" "$next"
}

remote_precheck() {
  local node=$1; shift
  test "$(id -u)" -ne 0 || fail 'timer precheck must be unprivileged'
  printf 'node=%s phase=timer_precheck\n' "$node"
  for timer in "$@"; do timer_precheck "$timer"; done
}

remote_finalize() {
  local node=$1 scope_validator=$2; shift 2
  test "$(id -u)" -eq 0 || fail 'remote finalizer requires root'
  printf 'node=%s phase=privileged_finalization\n' "$node"
  for timer in "$@"; do timer_precheck "$timer"; done
  validate_metric
  if test "$node" = choms-node-03; then
    test "$(stat -Lc '%U:%G:%a' "$PASSWORD_FILE")" = root:root:600 || fail 'Restic password metadata is invalid'
    check_once
    if report_is_valid; then
      echo 'repository_validation=passed execution=reused'
    else
      collect_repository_validation "$scope_validator"
      report_is_valid || fail 'repository validation report is invalid'
      echo 'repository_validation=passed execution=performed'
    fi
    sed -n -E '/^(restic_check|scope_validation|snapshots_hostname_tags|snapshot_[a-z0-9_]+|logical_bytes|stored_bytes|limit_bytes|limit_result|exclusion_[a-z_]+)=/p' "$REPORT"
  fi
  for timer in "$@"; do activate_timer "$timer"; done
}

remote_cleanup() {
  local target owner_uid
  test "$(id -u)" -ne 0 || fail 'remote staging cleanup must be unprivileged'
  owner_uid=$(id -u)
  for target in "$@"; do
    test -n "$target" || fail 'empty remote cleanup target'
    case "$target" in
      /tmp/choms-restic-finalize.*) ;;
      *) fail 'unsafe remote cleanup target' ;;
    esac
    if test -e "$target"; then
      test -f "$target" && test ! -L "$target" || fail 'remote cleanup target is not a regular file'
      test "$(stat -Lc '%u' "$target")" = "$owner_uid" || fail 'remote cleanup ownership mismatch'
      rm -f -- "$target"
    fi
  done
}

remote_validate() {
  local node=$1 next; shift
  test "$(id -u)" -ne 0 || fail 'validation must be unprivileged'
  validate_metric
  for timer in "$@"; do
    systemctl is-enabled --quiet "$timer" || fail "$timer is not enabled"
    systemctl is-active --quiet "$timer" || fail "$timer is not active"
    test "$(systemctl show "$timer" -p SubState --value)" = waiting || fail "$timer is not waiting"
    next=$(systemctl show "$timer" -p NextElapseUSecRealtime --value)
    test -n "$next" && test "$next" != n/a || fail "$timer has no next execution"
    printf 'node=%s timer=%s enabled=true active=true substate=waiting next=%s\n' "$node" "$timer" "$next"
  done
  if test "$node" = choms-node-03; then
    report_is_valid || fail 'repository validation report is unavailable'
    systemctl is-active --quiet ssh || fail 'sshd is not active'
    findmnt -n --mountpoint /var/lib/choms-restic/chroot/choms-platforms-restic >/dev/null || fail 'restricted bind mount is not active'
    echo 'node=choms-node-03 repository_validation=passed mount=active sshd=active'
  fi
}

ssh_noninteractive() {
  local address=$1; shift
  timeout 45s ssh -T "${SSH_OPTIONS[@]}" "chomsmaster@$address" "$@"
}

transfer_bundle() {
  local address=$1 destination=$2 scope_destination=$3
  [[ "$destination" =~ ^/tmp/choms-restic-finalize\.[0-9]+\.node(01|02|03)$ ]] || fail 'unsafe remote bundle path'
  [[ "$scope_destination" =~ ^/tmp/choms-restic-finalize\.[0-9]+\.node(01|02|03)\.scope\.py$ ]] || fail 'unsafe remote scope-validator path'
  scp -q "${SSH_OPTIONS[@]}" "$0" "chomsmaster@$address:$destination"
  scp -q "${SSH_OPTIONS[@]}" "$LOCAL_SCOPE_VALIDATOR" "chomsmaster@$address:$scope_destination"
  ssh_noninteractive "$address" chmod 0700 "$destination" "$scope_destination"
}

run_privileged() {
  local node=$1 address=$2 remote=$3 scope_validator=$4; shift 4
  local remote_command
  printf 'sudo_session=%s visible_authentication_max=1\n' "$node"
  printf -v remote_command 'sudo -- bash %q __remote-finalize %q %q' "$remote" "$node" "$scope_validator"
  while test "$#" -gt 0; do printf -v remote_command '%s %q' "$remote_command" "$1"; shift; done
  ssh -t "${SSH_OPTIONS[@]}" "chomsmaster@$address" "$remote_command" <"$TTY_DEVICE"
}

run_validation() {
  ssh_noninteractive 192.168.1.138 bash -s -- __remote-validate choms-node-01 choms-restic-backup-node01.timer <"$0"
  ssh_noninteractive 192.168.1.172 bash -s -- __remote-validate choms-node-02 choms-restic-backup-node02.timer <"$0"
  ssh_noninteractive 192.168.1.134 bash -s -- __remote-validate choms-node-03 choms-restic-backup-node03.timer choms-restic-maintenance.timer <"$0"
  echo 'final_validation=passed privileged=false backups_started_manually=false'
}

main_finalize() {
  local remote01=/tmp/choms-restic-finalize.$$.node01
  local remote02=/tmp/choms-restic-finalize.$$.node02
  local remote03=/tmp/choms-restic-finalize.$$.node03
  local scope01=${remote01}.scope.py scope02=${remote02}.scope.py scope03=${remote03}.scope.py
  test -n "$LOCAL_SCOPE_VALIDATOR" && test -x "$LOCAL_SCOPE_VALIDATOR" || fail 'local scope validator is unavailable'
  REMOTE_FILES=("192.168.1.138 $remote01 $scope01" "192.168.1.172 $remote02 $scope02" "192.168.1.134 $remote03 $scope03")
  trap cleanup_remote_files EXIT HUP INT TERM
  phase 'Transfer one non-sensitive finalizer bundle per node'
  transfer_bundle 192.168.1.138 "$remote01" "$scope01"
  transfer_bundle 192.168.1.172 "$remote02" "$scope02"
  transfer_bundle 192.168.1.134 "$remote03" "$scope03"
  phase 'Unprivileged Persistent=true catch-up gate on all timers'
  ssh_noninteractive 192.168.1.138 bash "$remote01" __remote-precheck choms-node-01 choms-restic-backup-node01.timer
  ssh_noninteractive 192.168.1.172 bash "$remote02" __remote-precheck choms-node-02 choms-restic-backup-node02.timer
  ssh_noninteractive 192.168.1.134 bash "$remote03" __remote-precheck choms-node-03 choms-restic-backup-node03.timer choms-restic-maintenance.timer
  phase 'One visible sudo session per node'
  run_privileged choms-node-03 192.168.1.134 "$remote03" "$scope03" choms-restic-backup-node03.timer choms-restic-maintenance.timer
  run_privileged choms-node-01 192.168.1.138 "$remote01" "$scope01" choms-restic-backup-node01.timer
  run_privileged choms-node-02 192.168.1.172 "$remote02" "$scope02" choms-restic-backup-node02.timer
  phase 'Idempotent unprivileged validation'
  run_validation
  echo 'encrypted_recovery_finalization=complete sudo_authentications_max=3 restic_check_executions_max=1 backups_started_manually=false'
}

cleanup_remote_files() {
  local rc=$? item address remote scope
  trap - EXIT HUP INT TERM
  for item in "${REMOTE_FILES[@]:-}"; do
    read -r address remote scope <<<"$item"
    test -n "$address" && test -n "$remote" && test -n "$scope" || continue
    ssh_noninteractive "$address" bash -s -- __remote-cleanup "$remote" "$scope" <"$0" >/dev/null 2>&1 || true
  done
  REMOTE_FILES=()
  exit "$rc"
}

cleanup_self_test() {
  local mode=$1 report=${CHOMS_CLEANUP_TEST_REPORT:-}
  REPOSITORY_WORK=''; REPOSITORY_WORK_OWNER_UID=''
  case "$mode" in
    uninitialized) cleanup_repository_work ;;
    normal|error)
      REPOSITORY_WORK=$(mktemp -d /tmp/choms-restic-finalize.XXXXXX)
      REPOSITORY_WORK_OWNER_UID=$(id -u)
      test -z "$report" || printf '%s\n' "$REPOSITORY_WORK" >"$report"
      trap cleanup_repository_work EXIT HUP INT TERM
      if test "$mode" = normal; then
        cleanup_repository_work
        trap - EXIT HUP INT TERM
      else
        return 97
      fi
      ;;
    *) return 2 ;;
  esac
}

case "${1:-}" in
  __remote-precheck) shift; remote_precheck "$@" ;;
  __remote-finalize) shift; remote_finalize "$@" ;;
  __remote-validate) shift; remote_validate "$@" ;;
  __remote-cleanup) shift; remote_cleanup "$@" ;;
  __test-cleanup) shift; cleanup_self_test "$@" ;;
  finalize|validate)
    test "$(id -u)" -ne 0 || fail 'run as chomsmaster, never root'
    test "$(id -un)" = chomsmaster || fail 'operator must be chomsmaster'
    test -z "${SUDO_ASKPASS:-}" || fail 'SUDO_ASKPASS is forbidden'
    test -r "$KNOWN_HOSTS" || fail 'operator known_hosts is unavailable'
    if test "$1" = finalize; then main_finalize; else run_validation; fi
    ;;
  *) usage ;;
esac
