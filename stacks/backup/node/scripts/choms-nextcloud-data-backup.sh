#!/usr/bin/env bash

set -euo pipefail
umask 077

export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

NAS_HOST=192.168.1.167
NAS_USER=chomsmaster
NAS_KEY=/home/chomsmaster/.ssh/choms_nas_backup
NAS_CONTROL=/usr/local/sbin/choms-nextcloud-backup-control.sh

STAMP="$(date +%Y%m%d-%H%M%S)"
LOCAL_DUMP="/tmp/mariadb-nextcloud-$STAMP.sql.gz"
REMOTE_DUMP="/tmp/mariadb-nextcloud-$STAMP.sql.gz"

MAINTENANCE_ENABLED=0

SSH=(
  ssh
  -i "$NAS_KEY"
  -o BatchMode=yes
  -o ConnectTimeout=15
  -o StrictHostKeyChecking=yes
  -o UserKnownHostsFile=/home/chomsmaster/.ssh/known_hosts
  "$NAS_USER@$NAS_HOST"
)

SCP=(
  scp
  -i "$NAS_KEY"
  -o BatchMode=yes
  -o ConnectTimeout=15
  -o StrictHostKeyChecking=yes
  -o UserKnownHostsFile=/home/chomsmaster/.ssh/known_hosts
)

fail() {
  echo "ERROR: $1"
  exit 1
}

maintenance_off() {
  if [ "$MAINTENANCE_ENABLED" -eq 1 ]; then
    echo "Desactivando mantenimiento..."

    kubectl exec \
      -n apps \
      "$NEXTCLOUD_POD" \
      -c nextcloud \
      -- php occ maintenance:mode --off \
      || true

    MAINTENANCE_ENABLED=0
  fi
}

cleanup() {
  status=$?

  maintenance_off
  rm -f "$LOCAL_DUMP"

  exit "$status"
}

trap cleanup EXIT INT TERM

exec 9>/run/lock/choms-nextcloud-data-backup.lock
flock -n 9 || fail "Ya existe otro backup en ejecución"

NEXTCLOUD_POD="$(
  kubectl get pod \
    -n apps \
    -l app=nextcloud \
    --field-selector=status.phase=Running \
    -o jsonpath='{.items[0].metadata.name}'
)"

MARIADB_POD="$(
  kubectl get pod \
    -n databases \
    -l app=mariadb \
    --field-selector=status.phase=Running \
    -o jsonpath='{.items[0].metadata.name}'
)"

test -n "$NEXTCLOUD_POD" || fail "No se encontró Nextcloud"
test -n "$MARIADB_POD" || fail "No se encontró MariaDB"

echo "Nextcloud: $NEXTCLOUD_POD"
echo "MariaDB:   $MARIADB_POD"
echo "Snapshot:  $STAMP"

echo
echo "Generando dump MariaDB local..."

kubectl exec \
  -n databases \
  "$MARIADB_POD" \
  -c mariadb \
  -- sh -eu -c '
    DB="${MARIADB_DATABASE:-${MYSQL_DATABASE:-nextcloud}}"
    USER="${MARIADB_USER:-${MYSQL_USER:-nextcloud}}"
    PASS="${MARIADB_PASSWORD:-${MYSQL_PASSWORD:-}}"

    test -n "$PASS"

    MYSQL_PWD="$PASS" exec mariadb-dump \
      --host=127.0.0.1 \
      --protocol=TCP \
      --user="$USER" \
      --single-transaction \
      --quick \
      --skip-lock-tables \
      "$DB"
  ' |
gzip -1 > "$LOCAL_DUMP"

test -s "$LOCAL_DUMP" || fail "Dump vacío"
gzip -t "$LOCAL_DUMP"

echo
echo "Preparando NAS..."

"${SSH[@]}" \
  "sudo '$NAS_CONTROL' prepare"

"${SCP[@]}" \
  "$LOCAL_DUMP" \
  "$NAS_USER@$NAS_HOST:$REMOTE_DUMP"

"${SSH[@]}" \
  "sudo '$NAS_CONTROL' install-dump '$REMOTE_DUMP'"

echo
echo "Activando mantenimiento..."

kubectl exec \
  -n apps \
  "$NEXTCLOUD_POD" \
  -c nextcloud \
  -- php occ maintenance:mode --on

MAINTENANCE_ENABLED=1

echo
echo "Creando snapshot reflink..."

"${SSH[@]}" \
  "sudo '$NAS_CONTROL' snapshot '$STAMP'"

maintenance_off

echo
echo "Validando snapshot..."

"${SSH[@]}" \
  "sudo '$NAS_CONTROL' validate '$STAMP'"

kubectl exec \
  -n apps \
  "$NEXTCLOUD_POD" \
  -c nextcloud \
  -- php occ status

curl -kfsS \
  https://nextcloud.chomsmaster.com/status.php

echo
echo
echo "Backup completado:"
echo "  /srv/storage/backups/homelab/nextcloud/daily/$STAMP"

trap - EXIT INT TERM
rm -f "$LOCAL_DUMP"
