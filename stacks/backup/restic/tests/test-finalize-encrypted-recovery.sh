#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
FINALIZER=$ROOT/finalize-encrypted-recovery.sh
SCOPE_VALIDATOR=$ROOT/scripts/choms-restic-validate-snapshot-scope.py
work=$(mktemp -d)
cleanup() { rm -rf -- "$work"; }
trap cleanup EXIT HUP INT TERM

test -x "$FINALIZER"
test -x "$SCOPE_VALIDATOR"
bash -n "$FINALIZER"

test "$(grep -Fc 'run_restic check' "$FINALIZER")" -eq 1
test "$(grep -Fc 'run_privileged choms-node-' "$FINALIZER")" -eq 3
test "$(grep -Fc "systemctl start \"\$timer\"" "$FINALIZER")" -eq 1
grep -Fq 'timer_catchup_risk=' "$FINALIZER"
grep -Fq 'action=stopped_before_activation' "$FINALIZER"
grep -Fq 'restic_check_executions_max=1' "$FINALIZER"
grep -Fq 'backups_started_manually=false' "$FINALIZER"
grep -Fq 'StrictHostKeyChecking=yes' "$FINALIZER"
grep -Fq 'substate=waiting' "$FINALIZER"
grep -Fq 'snapshot_node03=present' "$FINALIZER"
grep -Fq 'scope_validation=passed' "$FINALIZER"
grep -Fq 'restic_check=passed execution=reused' "$FINALIZER"
test "$(grep -Ec 'snapshot_choms_node_0[123]_node_0[123]_type_[a-z0-9_]+=present' "$FINALIZER")" -ge 6
for category in nextcloud_data multimedia downloads colegio personal_backups prometheus_tsdb loki; do
  grep -Fq "exclusion_${category}=passed" "$FINALIZER"
done
if grep -Eq 'sudo[[:space:]]+(-S|--stdin)|SUDO_ASKPASS=|systemctl start choms-restic-backup\.service|restic (backup|forget|prune|unlock)' "$FINALIZER"; then
  echo 'ERROR: forbidden finalizer action found' >&2
  exit 1
fi

scope_pass() {
  local name=$1 hostname=$2 host_tag=$3 type_tag=$4 logical_name=$5 fixture=$6
  python3 "$SCOPE_VALIDATOR" "$hostname" "$host_tag" "$type_tag" "$logical_name" \
    <"$fixture" >"$work/$name.output"
  grep -Fq "scope_validation=passed hostname=$hostname tags=$host_tag,$type_tag" "$work/$name.output"
}

scope_fail() {
  local name=$1 category=$2 hostname=$3 host_tag=$4 type_tag=$5 logical_name=$6 fixture=$7
  if python3 "$SCOPE_VALIDATOR" "$hostname" "$host_tag" "$type_tag" "$logical_name" \
    <"$fixture" >"$work/$name.output" 2>&1; then
    echo "ERROR: excluded scope accepted for $name" >&2
    exit 1
  fi
  grep -Fxq "scope_validation=failed category=$category" "$work/$name.output"
}

cat >"$work/k3s.jsonl" <<'EOF'
{"struct_type":"snapshot"}
{"struct_type":"node","type":"dir","path":"/"}
{"struct_type":"node","type":"dir","path":"/run"}
{"struct_type":"node","type":"dir","path":"/run/choms-restic.test"}
{"struct_type":"node","type":"file","path":"/run/choms-restic.test/state.db"}
{"struct_type":"node","type":"file","path":"/etc/choms-backup/recovery-sample.txt"}
EOF
scope_pass k3s choms-node-01 node-01 type-k3s - "$work/k3s.jsonl"

cat >"$work/secrets.jsonl" <<'EOF'
{"struct_type":"node","type":"dir","path":"/"}
{"struct_type":"node","type":"file","path":"/recovery-secrets.json"}
EOF
scope_pass secrets choms-node-01 node-01 type-secrets recovery-secrets.json "$work/secrets.jsonl"

cat >"$work/platform.jsonl" <<'EOF'
{"struct_type":"node","type":"dir","path":"/"}
{"struct_type":"node","type":"dir","path":"/data"}
{"struct_type":"node","type":"dir","path":"/data/backups"}
{"struct_type":"node","type":"dir","path":"/data/backups/kubernetes/20260830-031918"}
{"struct_type":"node","type":"file","path":"/data/backups/kubernetes/20260830-031918/validated.json"}
{"struct_type":"node","type":"file","path":"/mnt/choms-backups/scrutiny/logical/daily/latest/metadata.db"}
EOF
scope_pass platform choms-node-01 node-01 type-platform - "$work/platform.jsonl"

cat >"$work/nextcloud.jsonl" <<'EOF'
{"struct_type":"node","type":"dir","path":"/"}
{"struct_type":"node","type":"dir","path":"/mnt"}
{"struct_type":"node","type":"dir","path":"/mnt/choms-storage"}
{"struct_type":"node","type":"dir","path":"/mnt/choms-storage/kubernetes/apps-nextcloud-storage-pvc-2fbee8b2-917a-43ea-89e4-cf8d703ae466"}
{"struct_type":"node","type":"file","path":"/mnt/choms-storage/kubernetes/apps-nextcloud-storage-pvc-2fbee8b2-917a-43ea-89e4-cf8d703ae466/base.file"}
{"struct_type":"node","type":"file","path":"/mnt/choms-storage/kubernetes/apps-nextcloud-storage-pvc-2fbee8b2-917a-43ea-89e4-cf8d703ae466/config/config.php"}
{"struct_type":"node","type":"file","path":"/mnt/choms-storage/kubernetes/apps-nextcloud-storage-pvc-2fbee8b2-917a-43ea-89e4-cf8d703ae466/custom_apps/app.json"}
{"struct_type":"node","type":"file","path":"/mnt/choms-storage/kubernetes/apps-nextcloud-storage-pvc-2fbee8b2-917a-43ea-89e4-cf8d703ae466/themes/theme.json"}
EOF
scope_pass nextcloud choms-node-01 node-01 type-nextcloud - "$work/nextcloud.jsonl"

cat >"$work/jellyfin.jsonl" <<'EOF'
{"struct_type":"node","type":"dir","path":"/"}
{"struct_type":"node","type":"dir","path":"/data"}
{"struct_type":"node","type":"file","path":"/data/docker/jellyfin-node02/config/system.xml"}
EOF
scope_pass jellyfin choms-node-02 node-02 type-jellyfin - "$work/jellyfin.jsonl"

cat >"$work/qbittorrent.jsonl" <<'EOF'
{"struct_type":"node","type":"dir","path":"/"}
{"struct_type":"node","type":"dir","path":"/data"}
{"struct_type":"node","type":"file","path":"/data/docker/qbittorrent/config/settings.ini"}
EOF
scope_pass qbittorrent choms-node-03 node-03 type-qbittorrent - "$work/qbittorrent.jsonl"

cat >"$work/excluded-nextcloud.jsonl" <<'EOF'
{"struct_type":"node","type":"file","path":"/mnt/choms-storage/kubernetes/apps-nextcloud-storage-pvc-2fbee8b2-917a-43ea-89e4-cf8d703ae466/data/object.bin"}
EOF
scope_fail excluded-nextcloud nextcloud_data choms-node-01 node-01 type-nextcloud - "$work/excluded-nextcloud.jsonl"
cat >"$work/excluded-multimedia.jsonl" <<'EOF'
{"struct_type":"node","type":"file","path":"/data/docker/jellyfin-node02/config/cache/object.bin"}
EOF
scope_fail excluded-multimedia multimedia choms-node-02 node-02 type-jellyfin - "$work/excluded-multimedia.jsonl"
cat >"$work/excluded-downloads.jsonl" <<'EOF'
{"struct_type":"node","type":"file","path":"/data/docker/qbittorrent/downloads/object.bin"}
EOF
scope_fail excluded-downloads downloads choms-node-03 node-03 type-qbittorrent - "$work/excluded-downloads.jsonl"
cat >"$work/excluded-colegio.jsonl" <<'EOF'
{"struct_type":"node","type":"file","path":"/mnt/choms-storage/Colegio/object.bin"}
EOF
scope_fail excluded-colegio colegio choms-node-01 node-01 type-platform - "$work/excluded-colegio.jsonl"
cat >"$work/excluded-personal.jsonl" <<'EOF'
{"struct_type":"node","type":"file","path":"/srv/storage/backups/object.bin"}
EOF
scope_fail excluded-personal personal_backups choms-node-01 node-01 type-platform - "$work/excluded-personal.jsonl"
cat >"$work/excluded-historical.jsonl" <<'EOF'
{"struct_type":"node","type":"file","path":"/mnt/choms-storage/historical/object.bin"}
EOF
scope_fail excluded-historical personal_backups choms-node-01 node-01 type-platform - "$work/excluded-historical.jsonl"
cat >"$work/excluded-prometheus.jsonl" <<'EOF'
{"struct_type":"node","type":"file","path":"/mnt/choms-storage/kubernetes/prometheus-tsdb/object.bin"}
EOF
scope_fail excluded-prometheus prometheus_tsdb choms-node-01 node-01 type-platform - "$work/excluded-prometheus.jsonl"
cat >"$work/excluded-loki.jsonl" <<'EOF'
{"struct_type":"node","type":"file","path":"/mnt/choms-storage/kubernetes/loki/object.bin"}
EOF
scope_fail excluded-loki loki choms-node-01 node-01 type-platform - "$work/excluded-loki.jsonl"
scope_fail excluded-stdin-name stdin_logical_name choms-node-01 node-01 type-secrets unexpected.json "$work/secrets.jsonl"

printf '{malformed\n' >"$work/malformed.jsonl"
if python3 "$SCOPE_VALIDATOR" choms-node-01 node-01 type-platform - <"$work/malformed.jsonl" >"$work/technical.output" 2>&1; then
  echo 'ERROR: malformed scope metadata was accepted' >&2
  exit 1
fi
grep -Fxq 'scope_validation=error category=technical' "$work/technical.output"

CHOMS_CLEANUP_TEST_REPORT=$work/cleanup-normal "$FINALIZER" __test-cleanup normal
normal_target=$(<"$work/cleanup-normal")
test -n "$normal_target" && test ! -e "$normal_target"
CHOMS_CLEANUP_TEST_REPORT=$work/cleanup-error
export CHOMS_CLEANUP_TEST_REPORT
if "$FINALIZER" __test-cleanup error; then
  echo 'ERROR: cleanup error test unexpectedly succeeded' >&2
  exit 1
fi
error_target=$(<"$work/cleanup-error")
test -n "$error_target" && test ! -e "$error_target"
unset CHOMS_CLEANUP_TEST_REPORT
"$FINALIZER" __test-cleanup uninitialized
bash -s -- __test-cleanup uninitialized <"$FINALIZER"

mkdir -p "$work/timer-bin"
install -m 0644 /dev/null "$work/timer-unit"
cat >"$work/timer-bin/systemctl" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
case "$1" in
  is-enabled) exit 0 ;;
  is-active)
    if test "${2:-}" = --quiet; then exit 3; fi
    echo inactive
    exit 3
    ;;
  cat)
    printf '[Timer]\nOnCalendar=*-*-* 05:00:00 Europe/Madrid\nPersistent=true\n'
    ;;
  show)
    printf '%s\n' "$CHOMS_TEST_FRAGMENT"
    ;;
  *) exit 2 ;;
esac
SH
cat >"$work/timer-bin/systemd-analyze" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
printf '    Next elapse: %s\n' "$(/usr/bin/date -d "@$CHOMS_TEST_NEXT" '+%a %Y-%m-%d %H:%M:%S %Z')"
SH
cat >"$work/timer-bin/stat" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$CHOMS_TEST_BASELINE"
SH
cat >"$work/timer-bin/date" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
if test "$#" -eq 1 && test "$1" = +%s; then
  printf '%s\n' "$CHOMS_TEST_NOW"
else
  exec /usr/bin/date "$@"
fi
SH
chmod 0755 "$work/timer-bin/systemctl" "$work/timer-bin/systemd-analyze" "$work/timer-bin/stat" "$work/timer-bin/date"

CHOMS_TEST_FRAGMENT=$work/timer-unit CHOMS_TEST_BASELINE=1000 CHOMS_TEST_NOW=1500 CHOMS_TEST_NEXT=2000 \
  PATH="$work/timer-bin:$PATH" "$FINALIZER" __remote-precheck test choms-restic-backup-node01.timer >"$work/timer-safe"
grep -Fq 'result=safe' "$work/timer-safe"
if CHOMS_TEST_FRAGMENT=$work/timer-unit CHOMS_TEST_BASELINE=1000 CHOMS_TEST_NOW=1500 CHOMS_TEST_NEXT=1400 \
  PATH="$work/timer-bin:$PATH" "$FINALIZER" __remote-precheck test choms-restic-backup-node01.timer >"$work/timer-risk" 2>&1; then
  echo 'ERROR: missed persistent calendar was considered safe' >&2
  exit 1
fi
grep -Fq 'scheduled_elapse_after_unit_install_time' "$work/timer-risk"
if CHOMS_TEST_FRAGMENT=$work/timer-unit CHOMS_TEST_BASELINE=1000 CHOMS_TEST_NOW=1500 CHOMS_TEST_NEXT=1550 \
  PATH="$work/timer-bin:$PATH" "$FINALIZER" __remote-precheck test choms-restic-backup-node01.timer >"$work/timer-guard" 2>&1; then
  echo 'ERROR: activation guard did not stop the timer' >&2
  exit 1
fi
grep -Fq 'calendar_elapse_within_activation_guard' "$work/timer-guard"

mkdir -p "$work/bin" "$work/state"
cat >"$work/bin/ssh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
printf '%q ' "$@" >>"$CHOMS_TEST_LOG"
printf '\n' >>"$CHOMS_TEST_LOG"
if [[ " $* " == *" __remote-precheck "* ]]; then
  echo 'call=precheck' >>"$CHOMS_TEST_LOG"
  echo 'timer_precheck=test result=safe'
elif [[ " $* " == *" sudo -- bash "* ]]; then
  echo 'call=sudo' >>"$CHOMS_TEST_LOG"
  echo 'privileged_finalization=test result=passed'
elif [[ " $* " == *" __remote-validate "* ]]; then
  echo 'call=validate' >>"$CHOMS_TEST_LOG"
  echo 'final_validation=test result=passed'
fi
SH
cat >"$work/bin/scp" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
printf 'scp ' >>"$CHOMS_TEST_LOG"
printf '%q ' "$@" >>"$CHOMS_TEST_LOG"
printf '\n' >>"$CHOMS_TEST_LOG"
SH
cat >"$work/bin/timeout" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
shift
exec "$@"
SH
chmod 0755 "$work/bin/ssh" "$work/bin/scp" "$work/bin/timeout"
install -d -m 0700 "$work/.ssh"
install -m 0600 /dev/null "$work/.ssh/known_hosts"

CHOMS_TEST_LOG=$work/calls CHOMS_FINALIZER_TTY=/dev/null HOME=$work PATH="$work/bin:$PATH" "$FINALIZER" finalize >"$work/output"
test "$(grep -c 'sudo_session=choms-node-' "$work/output")" -eq 3
grep -Fq 'encrypted_recovery_finalization=complete' "$work/output"
test "$(grep -c '^call=sudo$' "$work/calls")" -eq 3
test "$(grep -c '^call=precheck$' "$work/calls")" -eq 3
test "$(grep -c '^call=validate$' "$work/calls")" -eq 3

: >"$work/calls"
CHOMS_TEST_LOG=$work/calls HOME=$work PATH="$work/bin:$PATH" "$FINALIZER" validate >"$work/validate-output"
test "$(grep -c '^call=validate$' "$work/calls")" -eq 3
if grep -q 'sudo --' "$work/calls"; then
  echo 'ERROR: validate opened a sudo session' >&2
  exit 1
fi
grep -Fq 'privileged=false' "$work/validate-output"

echo 'finalizer_tests=passed phases=precheck,privileged_finalize,unprivileged_validate scope_allowlists=6 exclusions=9 cleanup=normal,error,uninitialized catchup=safe,risk,guard sudo_sessions_max=3 restic_check_max=1'
