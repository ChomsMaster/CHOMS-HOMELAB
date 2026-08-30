#!/usr/bin/env bash
set -euo pipefail
set +x

validate_authorized_keys_file() {
  local staged=$1 prefix01 prefix02
  local -a lines
  test -f "$staged" || return 1
  mapfile -t lines <"$staged"
  test "${#lines[@]}" -eq 2
  prefix01='from="192.168.1.138",restrict,command="internal-sftp -d /choms-platforms-restic" ssh-ed25519 '
  prefix02='from="192.168.1.172",restrict,command="internal-sftp -d /choms-platforms-restic" ssh-ed25519 '
  [[ ${lines[0]} == "$prefix01"?* ]]
  [[ ${lines[1]} == "$prefix02"?* ]]
  ssh-keygen -lf "$staged" >/dev/null
}

case "${1:-}" in
  classify-repository)
    target=${2:-}
    test -n "$target" && test -d "$target" || exit 30
    shopt -s dotglob nullglob
    entries=("$target"/*)
    if test "${#entries[@]}" -eq 0; then
      exit 0
    fi
    for required_directory in data index keys locks snapshots; do
      if test ! -d "$target/$required_directory" || test -L "$target/$required_directory"; then
        exit 20
      fi
    done
    if test ! -f "$target/config" || test -L "$target/config"; then
      exit 20
    fi
    for entry in "${entries[@]}"; do
      case "${entry##*/}" in
        config|data|index|keys|locks|snapshots) ;;
        .choms-platforms-restic)
          if test ! -f "$entry" || test -L "$entry"; then exit 20; fi
          ;;
        *) exit 20 ;;
      esac
    done
    exit 10
    ;;

  file-matches)
    staged=${2:-} destination=${3:-} owner=${4:-} group=${5:-} mode=${6:-}
    test -f "$staged" && test -f "$destination" || exit 1
    cmp -s "$staged" "$destination" || exit 1
    test "$(stat -Lc '%U:%G:%a' "$destination")" = "$owner:$group:${mode#0}"
    ;;

  assert-stat)
    path=${2:-} expected=${3:-}
    test "$(stat -Lc '%U:%G:%a' "$path")" = "$expected"
    ;;

  install-authorized-keys)
    staged=${2:-} destination=${3:-}
    test "$destination" = /etc/ssh/authorized_keys/choms-restic || exit 1
    validate_authorized_keys_file "$staged"
    install -d -o root -g root -m 0755 /etc/ssh/authorized_keys
    temporary=$(mktemp /etc/ssh/authorized_keys/.choms-restic.XXXXXX)
    trap 'rm -f -- "$temporary"' EXIT HUP INT TERM
    install -o root -g root -m 0644 "$staged" "$temporary"
    mv -f -- "$temporary" "$destination"
    trap - EXIT HUP INT TERM
    test "$(stat -Lc '%U:%G:%a' /etc/ssh/authorized_keys)" = root:root:755
    test "$(stat -Lc '%U:%G:%a' "$destination")" = root:root:644
    echo 'authorized_keys_install=count=2 owner=root:root mode=0644'
    ;;

  validate-authorized-keys)
    validate_authorized_keys_file "${2:-}"
    echo 'authorized_keys_validation=count=2 result=passed'
    ;;

  snapshot-present)
    repository=${2:-} password_file=${3:-} host=${4:-} tag=${5:-}
    export RESTIC_REPOSITORY=$repository
    export RESTIC_PASSWORD_FILE=$password_file
    restic snapshots --json --host "$host" --tag "$tag" | grep -q '"id"'
    ;;

  probe-sftp)
    key=${2:-} known_hosts=${3:-} batch=${4:-}
    sftp -q -b "$batch" -i "$key" \
      -o BatchMode=yes -o NumberOfPasswordPrompts=0 \
      -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no \
      -o IdentitiesOnly=yes -o IdentityAgent=none \
      -o StrictHostKeyChecking=yes -o UserKnownHostsFile="$known_hosts" \
      choms-restic@192.168.1.134 >/dev/null 2>&1
    ;;

  expect-shell-denied|expect-pty-denied)
    probe=${1#expect-}
    key=${2:-} known_hosts=${3:-}
    tty_option=-T
    test "$probe" = pty-denied && tty_option=-tt
    if ssh "$tty_option" -i "$key" \
      -o BatchMode=yes -o NumberOfPasswordPrompts=0 \
      -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no \
      -o IdentitiesOnly=yes -o IdentityAgent=none \
      -o StrictHostKeyChecking=yes -o UserKnownHostsFile="$known_hosts" \
      choms-restic@192.168.1.134 true >/dev/null 2>&1; then
      echo "negative_probe=$probe result=unexpectedly_allowed" >&2
      exit 1
    fi
    echo "negative_probe=$probe result=denied_as_expected"
    ;;

  validate-sshd-effective)
    effective=$(/usr/sbin/sshd -T -C user=choms-restic,host=192.168.1.134,addr=192.168.1.138)
    for required in \
      'chrootdirectory /var/lib/choms-restic/chroot' \
      'forcecommand internal-sftp -d /choms-platforms-restic' \
      'authorizedkeysfile /etc/ssh/authorized_keys/choms-restic' \
      'passwordauthentication no' \
      'kbdinteractiveauthentication no' \
      'pubkeyauthentication yes' \
      'permittty no' \
      'allowtcpforwarding no' \
      'allowagentforwarding no' \
      'x11forwarding no' \
      'permittunnel no' \
      'gatewayports no'; do
      grep -Fxq "$required" <<<"$effective" || {
        echo 'sshd_effective_restrictions=failed' >&2
        exit 1
      }
    done
    echo 'sshd_effective_restrictions=passed authorized_keys_file=/etc/ssh/authorized_keys/choms-restic shell=forced_sftp pty=denied forwarding=denied tunnels=denied'
    ;;

  *) echo 'usage: choms-restic-remote-check.sh {classify-repository|file-matches|assert-stat|install-authorized-keys|validate-authorized-keys|snapshot-present|probe-sftp|expect-shell-denied|expect-pty-denied|validate-sshd-effective}' >&2; exit 2 ;;
esac
