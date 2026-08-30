#!/usr/bin/env bash
set -euo pipefail
set +x

confirm_literal() {
  local expected=$1 prompt=$2 attempt answer
  for attempt in 1 2 3; do
    IFS= read -r -p "$prompt" answer </dev/tty
    if test "$answer" = "$expected"; then unset answer; return 0; fi
    answer=; unset answer
    echo "confirmation_mismatch retry=$attempt/3" >/dev/tty
  done
  return 1
}

test "$(id -u)" -eq 0 || { echo 'ERROR: run with sudo' >&2; exit 1; }
node=${1:-}
case "$node" in choms-node-01|choms-node-02|choms-node-03) ;; *) echo 'ERROR: expected node name' >&2; exit 2 ;; esac
install -d -o root -g root -m 0700 /etc/choms-backup
find /etc/choms-backup -xdev -maxdepth 1 -type f -name '.restic-password.*' -delete
printf 'RESTIC PASSWORD FOR %s\n' "$node" >/dev/tty
IFS= read -r -s -p 'Password: ' first </dev/tty; echo >/dev/tty
IFS= read -r -s -p 'Repeat password: ' second </dev/tty; echo >/dev/tty
if test -z "$first" || test "$first" != "$second"; then
  unset first second
  echo 'ERROR: passwords differ or are empty' >&2
  exit 1
fi
if ! confirm_literal STORED 'External custody confirmation [TYPE STORED]: '; then
  unset first second
  echo 'ERROR: external custody not confirmed' >&2
  exit 1
fi
umask 077
temporary=$(mktemp /etc/choms-backup/.restic-password.XXXXXX)
cleanup() { rm -f -- "$temporary"; }
trap cleanup EXIT HUP INT TERM
printf '%s\n' "$first" >"$temporary"
unset first second
chmod 0600 "$temporary"
chown root:root "$temporary"
mv -f -- "$temporary" /etc/choms-backup/restic-password
trap - EXIT HUP INT TERM
install -d -o root -g root -m 0700 /var/lib/choms-restic-deploy
install -o root -g root -m 0600 /dev/null "/var/lib/choms-restic-deploy/password-$node.ready"
echo "password_install=$node result=passed owner=root:root mode=0600"
