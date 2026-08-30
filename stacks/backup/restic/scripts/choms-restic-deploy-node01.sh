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

NODE=choms-node-01
KEY=/root/.ssh/choms-restic-node01
KNOWN_HOSTS=/root/.ssh/choms-restic-known_hosts
REPOSITORY='sftp:choms-restic@192.168.1.134:/choms-platforms-restic'
MARKER=/var/tmp/choms-restic-validation-ready
FINALIZER=choms-restic-deploy-finalize-node01.service
TIMER=choms-restic-backup-node01.timer
SFTP_COMMAND='ssh -i /root/.ssh/choms-restic-node01 -o BatchMode=yes -o NumberOfPasswordPrompts=0 -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no -o IdentitiesOnly=yes -o IdentityAgent=none -o StrictHostKeyChecking=yes -o UserKnownHostsFile=/root/.ssh/choms-restic-known_hosts choms-restic@192.168.1.134 -s sftp'

run_restic() {
  RESTIC_REPOSITORY=$REPOSITORY RESTIC_PASSWORD_FILE=/etc/choms-backup/restic-password \
    restic -o "sftp.command=$SFTP_COMMAND" "$@"
}

snapshot_present() {
  run_restic snapshots --json --host "$1" --tag "$2" | grep -q '"id"'
}

repository_opens() {
  bundle_password_metadata_valid && run_restic snapshots --compact >/dev/null 2>&1
}

install_execute_support() {
  local payload=$SELF_DIR/payload
  test -d "$payload" || return 0
  bundle_install "$payload/choms-restic-key-install.sh" /usr/local/sbin/choms-restic-key-install.sh 0755
  bundle_install "$payload/choms-restic-remote-check.sh" /usr/local/libexec/choms-restic-remote-check.sh 0755
  bundle_install "$SELF_DIR/choms-restic-deploy-bundle-common.sh" /usr/local/lib/choms-restic-deploy-bundle-common.sh 0755
  bundle_install "$SELF_DIR/$(basename "${BASH_SOURCE[0]}")" /usr/local/sbin/choms-restic-deploy-node01.sh 0755
  bundle_install "$payload/choms-restic-deploy-finalize.service" "/etc/systemd/system/$FINALIZER" 0644
  systemd-analyze verify "/etc/systemd/system/$FINALIZER"
  systemctl daemon-reload
}

prepare() {
  local payload=$SELF_DIR/payload output=$SELF_DIR/output fingerprint
  bundle_phase "$NODE preparation"
  command -v restic >/dev/null
  test -f /var/lib/rancher/k3s/server/db/state.db || bundle_fail 'K3s SQLite state.db is absent'
  test ! -e /var/lib/rancher/k3s/server/db/etcd/member || bundle_fail 'K3s etcd datastore detected'
  if test -f /etc/rancher/k3s/config.yaml; then
    ! grep -Eq '^[[:space:]]*(datastore-endpoint|cluster-init):' /etc/rancher/k3s/config.yaml ||
      bundle_fail 'K3s external datastore or etcd initialization detected'
  fi
  install -d -o root -g root -m 0700 /root/.ssh /etc/choms-backup
  if test -e "$KEY"; then
    test -f "${KEY}.pub" || bundle_fail 'private key exists without public key'
  else
    test ! -e "${KEY}.pub" || bundle_fail 'orphan public key exists'
    ssh-keygen -q -t ed25519 -N '' -C "$NODE-restic" -f "$KEY"
  fi
  chmod 0600 "$KEY"; chmod 0644 "${KEY}.pub"
  bundle_install "$payload/node03.ed25519" "$KNOWN_HOSTS" 0600
  bundle_install "$payload/sftp-probe.batch" /etc/choms-backup/sftp-probe.batch 0600
  bundle_install "$payload/choms-restic-common.sh" /usr/local/lib/choms-restic-common.sh 0755
  bundle_install "$payload/choms-restic-key-install.sh" /usr/local/sbin/choms-restic-key-install.sh 0755
  bundle_install "$payload/choms-restic-backup.sh" /usr/local/sbin/choms-restic-backup.sh 0755
  bundle_install "$payload/recovery-sample.txt" /etc/choms-backup/recovery-sample.txt 0644
  bundle_install "$payload/choms-restic-backup.service" /etc/systemd/system/choms-restic-backup.service 0644
  bundle_install "$payload/choms-restic-backup.timer" "/etc/systemd/system/$TIMER" 0644
  bundle_install "$payload/choms-restic-remote-check.sh" /usr/local/libexec/choms-restic-remote-check.sh 0755
  bundle_install "$SELF_DIR/choms-restic-deploy-bundle-common.sh" /usr/local/lib/choms-restic-deploy-bundle-common.sh 0755
  bundle_install "$SELF_DIR/$(basename "${BASH_SOURCE[0]}")" /usr/local/sbin/choms-restic-deploy-node01.sh 0755
  bundle_install "$payload/choms-restic-deploy-finalize.service" "/etc/systemd/system/$FINALIZER" 0644
  systemd-analyze verify /etc/systemd/system/choms-restic-backup.service "/etc/systemd/system/$TIMER" "/etc/systemd/system/$FINALIZER"
  systemctl daemon-reload
  install -d -o chomsmaster -g chomsmaster -m 0700 "$output"
  install -o chomsmaster -g chomsmaster -m 0600 "${KEY}.pub" "$output/node01.pub"
  fingerprint=$(ssh-keygen -lf "${KEY}.pub" | awk '{print $2}')
  printf 'node=%s phase=prepare result=passed public_key_fingerprint=%s timer_enabled=%s\n' \
    "$NODE" "$fingerprint" "$(systemctl is-enabled "$TIMER" 2>/dev/null || true)"
}

execute() {
  bundle_phase "$NODE password, transport and first backup"
  install_execute_support
  if repository_opens; then
    echo "node=$NODE password_file=reused repository_access=passed"
  else
    bundle_install_password "$NODE"
    repository_opens || bundle_fail 'new password cannot open the initialized repository'
  fi
  if /usr/local/libexec/choms-restic-remote-check.sh probe-sftp "$KEY" "$KNOWN_HOSTS" /etc/choms-backup/sftp-probe.batch; then
    echo "transport_probe=$NODE result=passed"
  else
    echo "transport_probe=$NODE result=failed" >&2
    exit 1
  fi
  /usr/local/libexec/choms-restic-remote-check.sh expect-shell-denied "$KEY" "$KNOWN_HOSTS"
  /usr/local/libexec/choms-restic-remote-check.sh expect-pty-denied "$KEY" "$KNOWN_HOSTS"
  if snapshot_present choms-node-01 type-k3s && snapshot_present choms-node-01 type-secrets &&
     snapshot_present choms-node-01 type-platform && snapshot_present choms-node-01 type-nextcloud; then
    echo "node=$NODE first_backup=already_present"
  else
    /usr/local/sbin/choms-restic-backup.sh
  fi
  test -s /var/lib/node_exporter/textfile_collector/choms_restic_backup.prom
  if ! systemctl is-enabled --quiet "$TIMER"; then
    rm -f -- "$MARKER"
    systemctl reset-failed "$FINALIZER" 2>/dev/null || true
    systemctl start --no-block "$FINALIZER"
  fi
  echo "node=$NODE phase=execute result=passed timer_gate=waiting_for_global_validation"
}

finalize() {
  bundle_wait_for_validation_marker "$MARKER"
  repository_opens || bundle_fail 'repository is unavailable during timer finalization'
  for expected in 'choms-node-01 type-k3s' 'choms-node-01 type-secrets' 'choms-node-01 type-platform' 'choms-node-01 type-nextcloud' 'choms-node-02 type-jellyfin' 'choms-node-03 type-qbittorrent'; do
    read -r host tag <<<"$expected"
    snapshot_present "$host" "$tag" || bundle_fail "missing snapshot $host/$tag"
  done
  run_restic --retry-lock 20m check
  test -s /var/lib/node_exporter/textfile_collector/choms_restic_backup.prom
  systemctl enable "$TIMER"
  rm -f -- "$MARKER"
  echo "node=$NODE phase=finalize result=passed timer_enabled=true"
}

validate() {
  repository_opens || bundle_fail 'repository validation failed'
  test -s /var/lib/node_exporter/textfile_collector/choms_restic_backup.prom
  systemctl is-enabled --quiet "$TIMER"
  echo "node=$NODE phase=validate result=passed"
}

bundle_require_root "${1:-}"
case "${1:-}" in
  prepare) prepare ;;
  execute) execute ;;
  finalize) finalize ;;
  validate) validate ;;
  *) bundle_fail 'usage: choms-restic-deploy-node01.sh {prepare|execute|finalize|validate}' ;;
esac
