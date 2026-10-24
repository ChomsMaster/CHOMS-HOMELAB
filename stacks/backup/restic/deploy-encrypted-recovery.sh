#!/usr/bin/env bash
set -euo pipefail
set +x

fail() { echo "ERROR: $*" >&2; exit 1; }
phase() { printf '\n== %s ==\n' "$*"; }

test "$(id -u)" -ne 0 || fail 'run as chomsmaster, never root'
test "$(id -un)" = chomsmaster || fail 'operator must be chomsmaster'
test -z "${SUDO_ASKPASS:-}" || fail 'SUDO_ASKPASS is forbidden'

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
MODE=${1:-}
KNOWN_HOSTS=${HOME}/.ssh/known_hosts
REMOTE_MARKER=/var/tmp/choms-restic-validation-ready
NODES=('choms-node-01 192.168.1.138' 'choms-node-02 192.168.1.172' 'choms-node-03 192.168.1.134')
SSH_OPTIONS=(-o ConnectTimeout=10 -o ConnectionAttempts=1 -o ServerAliveInterval=15 -o ServerAliveCountMax=2 -o BatchMode=yes -o ForwardAgent=no -o IdentityAgent=none -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile="$KNOWN_HOSTS")

usage() { echo 'usage: deploy-encrypted-recovery.sh {fingerprints|deploy|resume-initialize|validate}' >&2; exit 2; }

scan_ed25519() {
  local name=$1 address=$2 destination=$3 raw=${3}.raw
  ssh-keyscan -T 5 -t ed25519 "$address" >"$raw" 2>/dev/null || true
  if ! awk -v address="$address" '
    /^[[:space:]]*#/ || /^[[:space:]]*$/ { next }
    $1 == address && $2 == "ssh-ed25519" && NF == 3 { valid++; print; next }
    { invalid++ }
    END { exit !(valid == 1 && invalid == 0) }
  ' "$raw" >"$destination"; then
    fail "expected exactly one Ed25519 host key for $name at $address"
  fi
  rm -f -- "$raw"
}

known_ed25519() {
  local address=$1
  test -f "$KNOWN_HOSTS" || return 0
  ssh-keygen -F "$address" -f "$KNOWN_HOSTS" 2>/dev/null | awk '$2 == "ssh-ed25519" {print $2 " " $3}' | sort -u
}

verify_pinned_hostkeys() {
  local node name address scanned candidate existing
  for node in "${NODES[@]}"; do
    read -r name address <<<"$node"
    scanned="$work_dir/$name.ed25519"; scan_ed25519 "$name" "$address" "$scanned"
    candidate=$(awk '{print $2 " " $3}' "$scanned"); existing=$(known_ed25519 "$address")
    test -n "$existing" || fail "no pinned Ed25519 known_hosts entry for $name"
    test "$(printf '%s\n' "$existing" | wc -l)" -eq 1 || fail "multiple pinned Ed25519 keys for $name"
    test "$existing" = "$candidate" || fail "live Ed25519 key differs from pinned key for $name"
  done
  echo 'host_identities=matched strict_host_key_checking=required'
}

ssh_admin() {
  local address=$1 remote_command
  shift; printf -v remote_command '%q ' "$@"
  timeout 30s ssh -T "${SSH_OPTIONS[@]}" "chomsmaster@$address" "$remote_command"
}

run_staged_bundle() {
  local node=$1 address=$2 remote_stage=$3 bundle_phase=$4 remote_command
  printf 'sudo_session=%s phase=%s visible_authentication_max=1\n' "$node" "$bundle_phase"
  printf -v remote_command 'sudo -- %q %q' "$remote_stage/bundle.sh" "$bundle_phase"
  ssh -t "${SSH_OPTIONS[@]}" "chomsmaster@$address" "$remote_command" </dev/tty
}

run_installed_bundle() {
  local node=$1 address=$2 script=$3 bundle_phase=$4 remote_command
  printf 'sudo_session=%s phase=%s visible_authentication_max=1\n' "$node" "$bundle_phase"
  printf -v remote_command 'sudo -- %q %q' "$script" "$bundle_phase"
  ssh -t "${SSH_OPTIONS[@]}" "chomsmaster@$address" "$remote_command" </dev/tty
}

make_origin_stage() {
  local node=$1 directory=$2 bundle=$3 backup=$4 timer=$5 finalizer=$6
  install -d -m 0700 "$directory/payload" "$directory/output"
  install -m 0755 "$ROOT/scripts/$bundle" "$directory/bundle.sh"
  install -m 0755 "$ROOT/scripts/choms-restic-deploy-bundle-common.sh" "$directory/choms-restic-deploy-bundle-common.sh"
  install -m 0755 "$ROOT/scripts/choms-restic-common.sh" "$directory/payload/choms-restic-common.sh"
  install -m 0755 "$ROOT/scripts/choms-restic-key-install.sh" "$directory/payload/choms-restic-key-install.sh"
  install -m 0755 "$ROOT/scripts/$backup" "$directory/payload/choms-restic-backup.sh"
  install -m 0755 "$ROOT/scripts/choms-restic-remote-check.sh" "$directory/payload/choms-restic-remote-check.sh"
  install -m 0644 "$ROOT/systemd/choms-restic-backup.service" "$directory/payload/choms-restic-backup.service"
  install -m 0644 "$ROOT/systemd/$timer" "$directory/payload/choms-restic-backup.timer"
  install -m 0644 "$ROOT/systemd/$finalizer" "$directory/payload/choms-restic-deploy-finalize.service"
  install -m 0600 "$work_dir/choms-node-03.ed25519" "$directory/payload/node03.ed25519"
  install -m 0600 "$ROOT/assets/sftp-probe.batch" "$directory/payload/sftp-probe.batch"
  if test "$node" = choms-node-01; then install -m 0644 "$ROOT/assets/recovery-sample.txt" "$directory/payload/recovery-sample.txt"; fi
}

make_origin_resume_stage() {
  local directory=$1 bundle=$2 finalizer=$3
  install -d -m 0700 "$directory/payload"
  install -m 0755 "$ROOT/scripts/$bundle" "$directory/bundle.sh"
  install -m 0755 "$ROOT/scripts/choms-restic-deploy-bundle-common.sh" "$directory/choms-restic-deploy-bundle-common.sh"
  install -m 0755 "$ROOT/scripts/choms-restic-key-install.sh" "$directory/payload/choms-restic-key-install.sh"
  install -m 0755 "$ROOT/scripts/choms-restic-remote-check.sh" "$directory/payload/choms-restic-remote-check.sh"
  install -m 0644 "$ROOT/systemd/$finalizer" "$directory/payload/choms-restic-deploy-finalize.service"
}

make_node03_stage() {
  local directory=$1 authorized_keys=$2
  install -d -m 0700 "$directory/payload"
  install -m 0755 "$ROOT/scripts/choms-restic-deploy-node03.sh" "$directory/bundle.sh"
  install -m 0755 "$ROOT/scripts/choms-restic-deploy-bundle-common.sh" "$directory/choms-restic-deploy-bundle-common.sh"
  install -m 0755 "$ROOT/scripts/choms-restic-common.sh" "$directory/payload/choms-restic-common.sh"
  install -m 0755 "$ROOT/scripts/choms-restic-key-install.sh" "$directory/payload/choms-restic-key-install.sh"
  install -m 0755 "$ROOT/scripts/choms-restic-backup-node03.sh" "$directory/payload/choms-restic-backup.sh"
  install -m 0755 "$ROOT/scripts/choms-restic-maintenance.sh" "$directory/payload/choms-restic-maintenance.sh"
  install -m 0755 "$ROOT/scripts/choms-restic-repository-control.sh" "$directory/payload/choms-restic-repository-control.sh"
  install -m 0755 "$ROOT/scripts/choms-restic-remote-check.sh" "$directory/payload/choms-restic-remote-check.sh"
  install -m 0644 "$ROOT/assets/recovery-sample.txt" "$directory/payload/recovery-sample.txt"
  install -m 0644 "$ROOT/sshd/choms-restic.conf" "$directory/payload/choms-restic.conf"
  install -m 0600 "$authorized_keys" "$directory/payload/authorized_keys"
  install -m 0644 "$ROOT/systemd/choms-restic-repository.mount" "$directory/payload/choms-restic-repository.mount"
  install -m 0644 "$ROOT/systemd/choms-restic-backup.service" "$directory/payload/choms-restic-backup.service"
  install -m 0644 "$ROOT/systemd/choms-restic-backup-node03.timer" "$directory/payload/choms-restic-backup.timer"
  install -m 0644 "$ROOT/systemd/choms-restic-maintenance.service" "$directory/payload/choms-restic-maintenance.service"
  install -m 0644 "$ROOT/systemd/choms-restic-maintenance.timer" "$directory/payload/choms-restic-maintenance.timer"
}

make_node03_resume_stage() {
  local directory=$1
  install -d -m 0700 "$directory/payload"
  install -m 0755 "$ROOT/scripts/choms-restic-deploy-node03.sh" "$directory/bundle.sh"
  install -m 0755 "$ROOT/scripts/choms-restic-deploy-bundle-common.sh" "$directory/choms-restic-deploy-bundle-common.sh"
  install -m 0755 "$ROOT/scripts/choms-restic-key-install.sh" "$directory/payload/choms-restic-key-install.sh"
  install -m 0755 "$ROOT/scripts/choms-restic-repository-control.sh" "$directory/payload/choms-restic-repository-control.sh"
  install -m 0755 "$ROOT/scripts/choms-restic-remote-check.sh" "$directory/payload/choms-restic-remote-check.sh"
  install -m 0644 "$ROOT/systemd/choms-restic-deploy-finalize-node03.service" "$directory/payload/choms-restic-deploy-finalize.service"
}

transfer_stage() {
  local address=$1 local_stage=$2 remote_stage=$3
  [[ "$remote_stage" =~ ^/tmp/choms-restic-deploy\.[0-9]+\.(node01|node02|node03)$ ]] || fail 'unsafe remote stage path'
  ssh_admin "$address" rm -rf -- "$remote_stage"
  ssh_admin "$address" install -d -m 0700 "$remote_stage"
  scp -q -r "${SSH_OPTIONS[@]}" "$local_stage/." "chomsmaster@$address:$remote_stage/"
  remote_stages+=("$address $remote_stage")
}

collect_public_key() {
  local node=$1 address=$2 remote_stage=$3 destination=$4 fingerprint
  scp -q "${SSH_OPTIONS[@]}" "chomsmaster@$address:$remote_stage/output/$node.pub" "$destination"
  awk 'NR == 1 && $1 == "ssh-ed25519" && NF >= 2 { valid++ } END { exit !(NR == 1 && valid == 1) }' "$destination" || fail "invalid public-key export from $node"
  fingerprint=$(ssh-keygen -lf "$destination" | awk '{print $2}')
  printf 'public_key=%s fingerprint=%s private_key_transferred=false\n' "$node" "$fingerprint"
}

signal_and_wait_for_timer() {
  local node=$1 address=$2 timer=$3 attempt
  if ssh_admin "$address" systemctl is-enabled --quiet "$timer"; then
    echo "node=$node post_validation_gate=already_complete timer_enabled=true"
    return 0
  fi
  ssh_admin "$address" rm -f -- "$REMOTE_MARKER"
  ssh_admin "$address" install -m 0600 /dev/null "$REMOTE_MARKER"
  for ((attempt = 0; attempt < 360; attempt++)); do
    if ssh_admin "$address" systemctl is-enabled --quiet "$timer"; then
      echo "node=$node post_validation_gate=passed timer_enabled=true"; return 0
    fi
    sleep 5
  done
  fail "$node finalizer did not enable its timer"
}

signal_and_wait_for_node03_validation() {
  local attempt marker=/var/tmp/choms-restic-origins-ready
  ssh_admin 192.168.1.134 rm -f -- "$marker"
  ssh_admin 192.168.1.134 install -m 0600 /dev/null "$marker"
  for ((attempt = 0; attempt < 720; attempt++)); do
    if ssh_admin 192.168.1.134 test -f /var/lib/choms-restic-deploy/validated &&
       ssh_admin 192.168.1.134 systemctl is-enabled --quiet choms-restic-backup-node03.timer &&
       ssh_admin 192.168.1.134 systemctl is-enabled --quiet choms-restic-maintenance.timer; then
      echo 'node=choms-node-03 background_validation=passed timers_enabled=true'
      return 0
    fi
    sleep 5
  done
  fail 'node-03 background validation did not complete'
}

case "$MODE" in fingerprints|deploy|resume-initialize|validate) ;; *) usage ;; esac
umask 077
work_dir=$(mktemp -d); remote_stages=()
cleanup() {
  local rc=$? item address remote_stage
  trap - EXIT HUP INT TERM
  for item in "${remote_stages[@]}"; do
    read -r address remote_stage <<<"$item"; ssh_admin "$address" rm -rf -- "$remote_stage" || true
  done
  rm -rf -- "$work_dir"; exit "$rc"
}
trap cleanup EXIT HUP INT TERM

case "$MODE" in
  fingerprints)
    install -d -m 0700 "${KNOWN_HOSTS%/*}"
    for node in "${NODES[@]}"; do
      read -r name address <<<"$node"; scanned="$work_dir/$name.ed25519"
      scan_ed25519 "$name" "$address" "$scanned"; fingerprint=$(ssh-keygen -lf "$scanned" | awk '{print $2}')
      printf '%s (%s) Ed25519 fingerprint: %s\n' "$name" "$address" "$fingerprint"
      read -r -p "Confirm $name fingerprint out of band [type CONFIRM $name]: " answer </dev/tty
      test "$answer" = "CONFIRM $name" || fail "$name host fingerprint not confirmed"
      existing=$(known_ed25519 "$address"); candidate=$(awk '{print $2 " " $3}' "$scanned")
      test -z "$existing" || test "$existing" = "$candidate" || fail "known_hosts conflict for $name"
      if test -z "$existing"; then cat "$scanned" >>"$KNOWN_HOSTS"; chmod 0600 "$KNOWN_HOSTS"; fi
    done
    echo 'host_fingerprints=confirmed strict_host_key_checking=required'
    ;;
  deploy)
    phase 'Read-only deployment preconditions'; verify_pinned_hostkeys
    for node in "${NODES[@]}"; do read -r name address <<<"$node"; ssh_admin "$address" command -v restic >/dev/null || fail "restic is unavailable on $name"; done
    mount_info=$(ssh_admin 192.168.1.134 findmnt -n -o TARGET,FSTYPE,OPTIONS -T /mnt/choms-local | tr -d '\r')
    read -r mount_target mount_type mount_options <<<"$mount_info"
    if test "$mount_target" != /mnt/choms-local || test "$mount_type" != ext4; then
      fail 'authorized ext4 mount is unavailable'
    fi
    [[ ",$mount_options," == *,rw,* ]] || fail 'authorized filesystem is not read-write'
    echo 'interactive_prompt_budget sudo_authentication=6 restic_password_entries=6 custody_confirmation_attempts=9 initialization_confirmation_attempts=3 total_maximum=24 normal_first_attempt=16'
    node01_local=$work_dir/node01; node02_local=$work_dir/node02; node03_local=$work_dir/node03
    node01_remote=/tmp/choms-restic-deploy.$$.node01; node02_remote=/tmp/choms-restic-deploy.$$.node02; node03_remote=/tmp/choms-restic-deploy.$$.node03
    make_origin_stage choms-node-01 "$node01_local" choms-restic-deploy-node01.sh choms-restic-backup-node01.sh choms-restic-backup-node01.timer choms-restic-deploy-finalize-node01.service
    make_origin_stage choms-node-02 "$node02_local" choms-restic-deploy-node02.sh choms-restic-backup-node02.sh choms-restic-backup-node02.timer choms-restic-deploy-finalize-node02.service
    transfer_stage 192.168.1.138 "$node01_local" "$node01_remote"; transfer_stage 192.168.1.172 "$node02_local" "$node02_remote"
    phase 'One privileged preparation bundle per origin'
    run_staged_bundle choms-node-01 192.168.1.138 "$node01_remote" prepare
    run_staged_bundle choms-node-02 192.168.1.172 "$node02_remote" prepare
    collect_public_key node01 192.168.1.138 "$node01_remote" "$work_dir/node01.pub"
    collect_public_key node02 192.168.1.172 "$node02_remote" "$work_dir/node02.pub"
    pub01=$(<"$work_dir/node01.pub"); pub02=$(<"$work_dir/node02.pub"); authorized_keys=$work_dir/authorized_keys
    printf 'from="192.168.1.138",restrict,command="internal-sftp -d /choms-platforms-restic" %s\n' "$pub01" >"$authorized_keys"
    printf 'from="192.168.1.172",restrict,command="internal-sftp -d /choms-platforms-restic" %s\n' "$pub02" >>"$authorized_keys"; unset pub01 pub02
    make_node03_stage "$node03_local" "$authorized_keys"; transfer_stage 192.168.1.134 "$node03_local" "$node03_remote"
    phase 'Single node-03 preparation and initialization session'
    run_staged_bundle choms-node-03 192.168.1.134 "$node03_remote" prepare
    phase 'Second and final privileged session per node'
    run_staged_bundle choms-node-01 192.168.1.138 "$node01_remote" execute
    ssh_admin 192.168.1.138 test -s /var/lib/node_exporter/textfile_collector/choms_restic_backup.prom
    run_staged_bundle choms-node-02 192.168.1.172 "$node02_remote" execute
    ssh_admin 192.168.1.172 test -s /var/lib/node_exporter/textfile_collector/choms_restic_backup.prom
    run_staged_bundle choms-node-03 192.168.1.134 "$node03_remote" execute
    phase 'Non-privileged release of post-validation timer gates'
    signal_and_wait_for_timer choms-node-01 192.168.1.138 choms-restic-backup-node01.timer
    signal_and_wait_for_timer choms-node-02 192.168.1.172 choms-restic-backup-node02.timer
    ssh_admin 192.168.1.134 systemctl is-enabled --quiet choms-restic-backup-node03.timer
    ssh_admin 192.168.1.134 systemctl is-enabled --quiet choms-restic-maintenance.timer
    echo 'deployment=complete sudo_authentications_max=6 monitoring_helm=not_applied forget=disabled prune=disabled unlock=disabled'
    ;;
  resume-initialize)
    phase 'Resume directly from the rejected initialization gate'
    verify_pinned_hostkeys
    echo 'interactive_prompt_budget_remaining sudo_authentication=3 restic_password_entries=6 custody_confirmation_attempts=9 initialization_confirmation_attempts=3 total_maximum=21'
    node01_local=$work_dir/node01-resume; node02_local=$work_dir/node02-resume; node03_local=$work_dir/node03-resume
    node01_remote=/tmp/choms-restic-deploy.$$.node01; node02_remote=/tmp/choms-restic-deploy.$$.node02; node03_remote=/tmp/choms-restic-deploy.$$.node03
    make_origin_resume_stage "$node01_local" choms-restic-deploy-node01.sh choms-restic-deploy-finalize-node01.service
    make_origin_resume_stage "$node02_local" choms-restic-deploy-node02.sh choms-restic-deploy-finalize-node02.service
    make_node03_resume_stage "$node03_local"
    transfer_stage 192.168.1.138 "$node01_local" "$node01_remote"
    transfer_stage 192.168.1.172 "$node02_local" "$node02_remote"
    transfer_stage 192.168.1.134 "$node03_local" "$node03_remote"
    run_staged_bundle choms-node-03 192.168.1.134 "$node03_remote" resume-initialize
    run_staged_bundle choms-node-01 192.168.1.138 "$node01_remote" execute
    ssh_admin 192.168.1.138 test -s /var/lib/node_exporter/textfile_collector/choms_restic_backup.prom
    run_staged_bundle choms-node-02 192.168.1.172 "$node02_remote" execute
    ssh_admin 192.168.1.172 test -s /var/lib/node_exporter/textfile_collector/choms_restic_backup.prom
    signal_and_wait_for_node03_validation
    signal_and_wait_for_timer choms-node-01 192.168.1.138 choms-restic-backup-node01.timer
    signal_and_wait_for_timer choms-node-02 192.168.1.172 choms-restic-backup-node02.timer
    echo 'deployment=complete resumed_from=initialization_gate sudo_authentications_max=3 monitoring_helm=not_applied'
    ;;
  validate)
    verify_pinned_hostkeys
    run_installed_bundle choms-node-01 192.168.1.138 /usr/local/sbin/choms-restic-deploy-node01.sh validate
    run_installed_bundle choms-node-02 192.168.1.172 /usr/local/sbin/choms-restic-deploy-node02.sh validate
    run_installed_bundle choms-node-03 192.168.1.134 /usr/local/sbin/choms-restic-deploy-node03.sh validate
    echo 'deployment_validation=passed read_only=true sudo_authentications_max=3'
    ;;
esac
