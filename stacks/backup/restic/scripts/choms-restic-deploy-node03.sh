#!/usr/bin/env bash
set -euo pipefail
set +x

SELF_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
if test -f "$SELF_DIR/choms-restic-deploy-bundle-common.sh"; then
  # shellcheck disable=SC1091
  source "$SELF_DIR/choms-restic-deploy-bundle-common.sh"
else
  # shellcheck source=/dev/null
  source /usr/local/lib/choms-restic-deploy-bundle-common.sh
fi

NODE=choms-node-03
REPOSITORY=/mnt/choms-local/backups/choms-platforms-restic
CHROOT=/var/lib/choms-restic/chroot
CHROOT_REPOSITORY=$CHROOT/choms-platforms-restic
VALIDATED_MARKER=/var/lib/choms-restic-deploy/validated
ORIGINS_READY_MARKER=/var/tmp/choms-restic-origins-ready
FINALIZER=choms-restic-deploy-finalize-node03.service
MOUNT_UNIT=$(systemd-escape --path --suffix=mount "$CHROOT_REPOSITORY")

run_restic() {
  RESTIC_REPOSITORY=$REPOSITORY RESTIC_PASSWORD_FILE=/etc/choms-backup/restic-password restic "$@"
}
snapshot_present() { run_restic snapshots --json --host "$1" --tag "$2" | grep -q '"id"'; }
repository_opens() { bundle_password_metadata_valid && run_restic snapshots --compact >/dev/null 2>&1; }

classify_repository() {
  local helper=$1 status
  if bash "$helper" classify-repository "$REPOSITORY"; then status=0; else status=$?; fi
  case "$status" in
    0) echo EMPTY ;;
    10) echo RESTIC ;;
    20) echo UNKNOWN ;;
    *) echo ERROR ;;
  esac
}

validate_mount() {
  local target root options
  read -r target root options < <(findmnt -n -o TARGET,FSROOT,OPTIONS --mountpoint "$CHROOT_REPOSITORY")
  test "$target" = "$CHROOT_REPOSITORY" || bundle_fail 'bind mount target mismatch'
  test "$root" = /backups/choms-platforms-restic || bundle_fail 'bind mount source mismatch'
  [[ ",$options," == *,rw,* ]] || bundle_fail 'bind mount is not read-write'
}

prepare_destination() {
  local payload=$SELF_DIR/payload passwd_by_uid passwd_by_name group_by_gid group_by_name
  local classification sshd_changed=0
  bundle_phase "$NODE destination, sshd and declarative installation"
  command -v restic >/dev/null
  if test -e "$REPOSITORY"; then
    classification=$(classify_repository "$payload/choms-restic-remote-check.sh")
  else
    classification=ABSENT
  fi
  case "$classification" in
    ABSENT|EMPTY|RESTIC) ;;
    UNKNOWN) bundle_fail 'repository target contains unknown data' ;;
    *) bundle_fail 'unable to classify repository target' ;;
  esac
  [[ "$MOUNT_UNIT" =~ ^[^/[:space:]]+\.mount$ ]] || bundle_fail 'invalid escaped mount-unit basename'
  passwd_by_uid=$(getent passwd 980 || true); passwd_by_name=$(getent passwd choms-restic || true)
  group_by_gid=$(getent group 980 || true); group_by_name=$(getent group choms-restic || true)
  if test -n "$passwd_by_uid" && [[ "$passwd_by_uid" != choms-restic:* ]]; then bundle_fail 'UID 980 conflict'; fi
  if test -n "$passwd_by_name" && [[ "$passwd_by_name" != choms-restic:x:980:980:* ]]; then bundle_fail 'unexpected choms-restic UID/GID'; fi
  if test -n "$group_by_gid" && [[ "$group_by_gid" != choms-restic:* ]]; then bundle_fail 'GID 980 conflict'; fi
  if test -n "$group_by_name" && [[ "$group_by_name" != choms-restic:x:980:* ]]; then bundle_fail 'unexpected choms-restic GID'; fi
  test -n "$group_by_name" || groupadd --gid 980 choms-restic
  if test -z "$passwd_by_name"; then
    useradd --uid 980 --gid 980 --home-dir /var/lib/choms-restic --create-home --shell /usr/sbin/nologin choms-restic
    passwd --lock choms-restic
  fi
  install -d -o root -g root -m 0711 /mnt/choms-local/backups
  install -d -o choms-restic -g choms-restic -m 0700 "$REPOSITORY"
  chown root:root /var/lib/choms-restic; chmod 0711 /var/lib/choms-restic
  install -d -o root -g root -m 0755 "$CHROOT"
  if findmnt -n --mountpoint "$CHROOT_REPOSITORY" >/dev/null; then
    validate_mount
  else
    install -d -o root -g root -m 0755 "$CHROOT_REPOSITORY"
  fi
  install -d -o root -g root -m 0700 /etc/choms-backup
  for component in / /var /var/lib /var/lib/choms-restic "$CHROOT"; do
    test "$(stat -Lc '%U:%G' "$component")" = root:root || bundle_fail "$component is not root-owned"
    mode=$(stat -Lc '%a' "$component")
    (( (8#$mode & 0022) == 0 )) || bundle_fail "$component is group/other writable"
  done
  bundle_assert_stat "$REPOSITORY" choms-restic:choms-restic:700
  bundle_install "$payload/choms-restic-repository.mount" "/etc/systemd/system/$MOUNT_UNIT" 0644
  systemd-analyze verify "/etc/systemd/system/$MOUNT_UNIT"
  systemctl daemon-reload
  if ! systemctl is-enabled --quiet "$MOUNT_UNIT" || ! systemctl is-active --quiet "$MOUNT_UNIT"; then
    systemctl enable --now "$MOUNT_UNIT"
  fi
  validate_mount

  bash "$payload/choms-restic-remote-check.sh" validate-authorized-keys "$payload/authorized_keys" >/dev/null
  /usr/sbin/sshd -t -f "$payload/choms-restic.conf"
  install -d -o root -g root -m 0755 /etc/ssh/authorized_keys
  bash "$payload/choms-restic-remote-check.sh" install-authorized-keys "$payload/authorized_keys" /etc/ssh/authorized_keys/choms-restic
  if ! cmp -s "$payload/choms-restic.conf" /etc/ssh/sshd_config.d/choms-restic.conf; then sshd_changed=1; fi
  bundle_install "$payload/choms-restic.conf" /etc/ssh/sshd_config.d/choms-restic.conf 0644
  /usr/sbin/sshd -t
  bundle_install "$payload/choms-restic-remote-check.sh" /usr/local/libexec/choms-restic-remote-check.sh 0755
  /usr/local/libexec/choms-restic-remote-check.sh validate-sshd-effective
  if test "$sshd_changed" -eq 1; then systemctl reload ssh; fi

  bundle_install "$payload/choms-restic-common.sh" /usr/local/lib/choms-restic-common.sh 0755
  bundle_install "$payload/choms-restic-key-install.sh" /usr/local/sbin/choms-restic-key-install.sh 0755
  bundle_install "$payload/choms-restic-backup.sh" /usr/local/sbin/choms-restic-backup.sh 0755
  bundle_install "$payload/choms-restic-maintenance.sh" /usr/local/sbin/choms-restic-maintenance.sh 0755
  bundle_install "$payload/choms-restic-repository-control.sh" /usr/local/sbin/choms-restic-repository-control.sh 0755
  bundle_install "$payload/recovery-sample.txt" /etc/choms-backup/recovery-sample.txt 0644
  bundle_install "$payload/choms-restic-backup.service" /etc/systemd/system/choms-restic-backup.service 0644
  bundle_install "$payload/choms-restic-backup.timer" /etc/systemd/system/choms-restic-backup-node03.timer 0644
  bundle_install "$payload/choms-restic-maintenance.service" /etc/systemd/system/choms-restic-maintenance.service 0644
  bundle_install "$payload/choms-restic-maintenance.timer" /etc/systemd/system/choms-restic-maintenance.timer 0644
  bundle_install "$SELF_DIR/choms-restic-deploy-bundle-common.sh" /usr/local/lib/choms-restic-deploy-bundle-common.sh 0755
  bundle_install "$SELF_DIR/$(basename "${BASH_SOURCE[0]}")" /usr/local/sbin/choms-restic-deploy-node03.sh 0755
  systemd-analyze verify /etc/systemd/system/choms-restic-backup.service /etc/systemd/system/choms-restic-backup-node03.timer /etc/systemd/system/choms-restic-maintenance.service /etc/systemd/system/choms-restic-maintenance.timer "/etc/systemd/system/$MOUNT_UNIT"
  systemctl daemon-reload

  if test "$classification" = ABSENT; then classification=EMPTY; fi
  case "$classification" in
    EMPTY)
      echo 'repository_target=EMPTY password_rotation=required_before_initialization'
      if bundle_password_install_evidence "$NODE"; then
        echo 'password_install_evidence=present password_rotation=skipped'
      else
        bundle_install_password "$NODE"
      fi
      bundle_clear_before_initialize
      printf 'repository_path=%s\nrepository_state=EMPTY\npassword_input=finished\n' "$REPOSITORY" >/dev/tty
      if ! bundle_confirm_literal 'INITIALIZE choms-platforms-restic' 'TYPE INITIALIZE choms-platforms-restic: '; then
        bundle_fail 'repository initialization not confirmed'
      fi
      /usr/local/sbin/choms-restic-repository-control.sh init
      ;;
    RESTIC)
      if repository_opens; then
        echo 'repository_target=RESTIC initialization=skipped password_file=reused'
      else
        bundle_install_password "$NODE"
        repository_opens || bundle_fail 'new password cannot open existing repository; repository unchanged'
      fi
      ;;
    *) bundle_fail 'repository classification changed unexpectedly during preparation' ;;
  esac
  repository_opens || bundle_fail 'node-03 cannot open repository after preparation'
  printf 'node=%s phase=prepare result=passed repository=initialized_or_reused timer_enabled=%s\n' \
    "$NODE" "$(systemctl is-enabled choms-restic-backup-node03.timer 2>/dev/null || true)"
}

install_resume_support() {
  local payload=$SELF_DIR/payload
  bundle_install "$payload/choms-restic-key-install.sh" /usr/local/sbin/choms-restic-key-install.sh 0755
  bundle_install "$payload/choms-restic-repository-control.sh" /usr/local/sbin/choms-restic-repository-control.sh 0755
  bundle_install "$SELF_DIR/choms-restic-deploy-bundle-common.sh" /usr/local/lib/choms-restic-deploy-bundle-common.sh 0755
  bundle_install "$SELF_DIR/$(basename "${BASH_SOURCE[0]}")" /usr/local/sbin/choms-restic-deploy-node03.sh 0755
  bundle_install "$payload/choms-restic-deploy-finalize.service" "/etc/systemd/system/$FINALIZER" 0644
  systemd-analyze verify "/etc/systemd/system/$FINALIZER"
  systemctl daemon-reload
}

resume_initialize() {
  local payload=$SELF_DIR/payload classification
  bundle_phase "$NODE resume directly at repository initialization"
  classification=$(classify_repository "$payload/choms-restic-remote-check.sh")
  case "$classification" in
    EMPTY)
      install_resume_support
      if bundle_password_install_evidence "$NODE"; then
        echo 'password_install_evidence=present password_rotation=skipped'
      else
        echo 'password_install_evidence=absent password_rotation=required_once'
        bundle_install_password "$NODE"
      fi
      bundle_clear_before_initialize
      printf 'repository_path=%s\nrepository_state=EMPTY\npassword_input=finished\n' "$REPOSITORY" >/dev/tty
      if ! bundle_confirm_literal 'INITIALIZE choms-platforms-restic' 'TYPE INITIALIZE choms-platforms-restic: '; then
        bundle_fail 'repository initialization not confirmed after three attempts'
      fi
      /usr/local/sbin/choms-restic-repository-control.sh init
      ;;
    RESTIC)
      install_resume_support
      repository_opens || bundle_fail 'existing repository does not open with node-03 password; repository unchanged'
      echo 'repository_target=RESTIC initialization=already_complete'
      ;;
    UNKNOWN) bundle_fail 'repository target contains unknown data' ;;
    *) bundle_fail 'unable to classify repository target' ;;
  esac
  repository_opens || bundle_fail 'node-03 cannot open repository after initialization gate'
  if ! systemctl is-enabled --quiet choms-restic-backup-node03.timer; then
    rm -f -- "$ORIGINS_READY_MARKER"
    systemctl reset-failed "$FINALIZER" 2>/dev/null || true
    systemctl start --no-block "$FINALIZER"
  fi
  echo 'node=choms-node-03 phase=resume-initialize result=passed finalizer=waiting_for_origins'
}

execute_and_validate() {
  local restore_target=/run/choms-restic-restore-sample
  bundle_phase "$NODE final backup and global validation"
  repository_opens || bundle_fail 'node-03 cannot open repository'
  for expected in 'choms-node-01 type-k3s' 'choms-node-01 type-secrets' 'choms-node-01 type-platform' 'choms-node-01 type-nextcloud' 'choms-node-02 type-jellyfin'; do
    read -r host tag <<<"$expected"
    snapshot_present "$host" "$tag" || bundle_fail "missing prerequisite snapshot $host/$tag"
  done
  if snapshot_present choms-node-03 type-qbittorrent; then
    echo "node=$NODE first_backup=already_present"
  else
    /usr/local/sbin/choms-restic-backup.sh
  fi
  run_restic --retry-lock 20m check
  for expected in 'choms-node-01 type-k3s' 'choms-node-01 type-secrets' 'choms-node-01 type-platform' 'choms-node-01 type-nextcloud' 'choms-node-02 type-jellyfin' 'choms-node-03 type-qbittorrent'; do
    read -r host tag <<<"$expected"
    snapshot_present "$host" "$tag" || bundle_fail "missing snapshot $host/$tag"
  done
  test ! -e "$restore_target" || bundle_fail 'exact restore-test target already exists'
  install -d -o root -g root -m 0700 "$restore_target"
  cleanup_restore() { rm -rf -- "$restore_target"; }
  trap cleanup_restore EXIT HUP INT TERM
  run_restic restore latest --host choms-node-01 --tag type-k3s --include /etc/choms-backup/recovery-sample.txt --target "$restore_target"
  cmp -s /etc/choms-backup/recovery-sample.txt "$restore_target/etc/choms-backup/recovery-sample.txt" || bundle_fail 'restore sample mismatch'
  cleanup_restore; trap - EXIT HUP INT TERM
  test -s /var/lib/node_exporter/textfile_collector/choms_restic_backup.prom
  rm -f -- /var/lib/choms-restic/.ssh/authorized_keys
  systemctl enable choms-restic-backup-node03.timer choms-restic-maintenance.timer
  install -d -o root -g root -m 0755 /var/lib/choms-restic-deploy
  install -o root -g root -m 0644 /dev/null "$VALIDATED_MARKER"
  echo "node=$NODE phase=execute result=passed global_validation=passed timers_enabled=true"
}

validate() {
  repository_opens || bundle_fail 'repository validation failed'
  run_restic --no-lock check
  systemctl is-enabled --quiet choms-restic-backup-node03.timer
  systemctl is-enabled --quiet choms-restic-maintenance.timer
  systemctl is-active --quiet "$MOUNT_UNIT"
  test -s /var/lib/node_exporter/textfile_collector/choms_restic_backup.prom
  echo "node=$NODE phase=validate result=passed"
}

finalize() {
  bundle_wait_for_validation_marker "$ORIGINS_READY_MARKER"
  execute_and_validate
  rm -f -- "$ORIGINS_READY_MARKER"
}

bundle_require_root "${1:-}"
case "${1:-}" in
  prepare) prepare_destination ;;
  execute) execute_and_validate ;;
  resume-initialize) resume_initialize ;;
  finalize) finalize ;;
  validate) validate ;;
  *) bundle_fail 'usage: choms-restic-deploy-node03.sh {prepare|execute|resume-initialize|finalize|validate}' ;;
esac
