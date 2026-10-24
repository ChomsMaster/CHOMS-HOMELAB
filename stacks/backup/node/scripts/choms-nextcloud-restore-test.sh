#!/usr/bin/env bash

set -euo pipefail
umask 077

export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

NAS_HOST=192.168.1.167
NAS_USER=chomsmaster
NAS_KEY=/home/chomsmaster/.ssh/choms_nas_backup
NAS_CONTROL=/usr/local/sbin/choms-nextcloud-backup-control.sh

NS=databases
POD=nextcloud-mariadb-restore-test

RUN_STAMP="$(date +%Y%m%d-%H%M%S)"
REMOTE_DUMP="/tmp/mariadb-nextcloud-$RUN_STAMP.sql.gz"
LOCAL_DUMP="/tmp/mariadb-nextcloud-restore-$RUN_STAMP.sql.gz"
RESTORE_ROOT_PASSWORD="$(openssl rand -hex 24)"

MARIADB_POD="$(
  kubectl get pod \
    -n databases \
    -l app=mariadb \
    --field-selector=status.phase=Running \
    -o jsonpath='{.items[0].metadata.name}'
)"

test -n "$MARIADB_POD"

MARIADB_IMAGE="$(
  kubectl get pod "$MARIADB_POD" \
    -n databases \
    -o jsonpath='{.status.containerStatuses[?(@.name=="mariadb")].imageID}'
)"

test -n "$MARIADB_IMAGE"

if [[ "$MARIADB_IMAGE" != *@sha256:* ]]; then
  echo "ERROR: MariaDB runtime no expone un imageID inmutable." >&2
  exit 1
fi

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

cleanup() {
  kubectl delete pod "$POD" \
    -n "$NS" \
    --ignore-not-found=true \
    --wait=false \
    >/dev/null 2>&1 || true

  "${SSH[@]}" "rm -f '$REMOTE_DUMP'" \
    >/dev/null 2>&1 || true

  rm -f "$LOCAL_DUMP"
}

trap cleanup EXIT INT TERM

fail() {
  echo
  echo "ERROR: $1"
  exit 1
}

echo "=================================================="
echo " NEXTCLOUD RESTORE DRY-RUN"
echo "=================================================="
echo "Inicio: $(date --iso-8601=seconds)"

echo
echo "========== 1. VALIDAR SNAPSHOT =========="

"${SSH[@]}" \
  "sudo '$NAS_CONTROL' latest"

echo
echo "========== 2. CLONAR ARCHIVOS =========="

"${SSH[@]}" \
  "sudo '$NAS_CONTROL' restore-test latest"

echo
echo "========== 3. EXPORTAR DUMP =========="

"${SSH[@]}" \
  "sudo '$NAS_CONTROL' export-dump latest '$REMOTE_DUMP'"

"${SCP[@]}" \
  "$NAS_USER@$NAS_HOST:$REMOTE_DUMP" \
  "$LOCAL_DUMP"

test -s "$LOCAL_DUMP" \
  || fail "El dump exportado está vacío"

gzip -t "$LOCAL_DUMP" \
  || fail "El dump exportado está dañado"

echo "Dump válido:"
ls -lh "$LOCAL_DUMP"

echo
echo "========== 4. CREAR MARIADB TEMPORAL =========="

kubectl delete pod "$POD" \
  -n "$NS" \
  --ignore-not-found=true \
  --wait=true \
  >/dev/null 2>&1 || true

kubectl run "$POD" \
  -n "$NS" \
  --image="$MARIADB_IMAGE" \
  --restart=Never \
  --env="MARIADB_ROOT_PASSWORD=$RESTORE_ROOT_PASSWORD" \
  --env=MARIADB_DATABASE=nextcloud_restore

kubectl wait \
  -n "$NS" \
  --for=condition=Ready \
  "pod/$POD" \
  --timeout=180s

for attempt in $(seq 1 60); do
  if kubectl exec \
    -n "$NS" \
    "$POD" \
    -- mariadb-admin \
      --host=127.0.0.1 \
      --protocol=TCP \
      --user=root \
      --password="$RESTORE_ROOT_PASSWORD" \
      ping \
      --silent \
      >/dev/null 2>&1
  then
    break
  fi

  if [ "$attempt" -eq 60 ]; then
    fail "MariaDB temporal no terminó de inicializar"
  fi

  sleep 2
done

echo
echo "========== 5. RESTAURAR DUMP =========="

gzip -dc "$LOCAL_DUMP" |
kubectl exec \
  -i \
  -n "$NS" \
  "$POD" \
  -- mariadb \
    --host=127.0.0.1 \
    --protocol=TCP \
    --user=root \
    --password="$RESTORE_ROOT_PASSWORD" \
    nextcloud_restore

echo
echo "========== 6. VALIDAR DATOS =========="

TABLE_COUNT="$(
  kubectl exec \
    -n "$NS" \
    "$POD" \
    -- mariadb \
      --host=127.0.0.1 \
      --protocol=TCP \
      --user=root \
      --password="$RESTORE_ROOT_PASSWORD" \
      --batch \
      --skip-column-names \
      --execute='
        SELECT COUNT(*)
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = "nextcloud_restore";
      ' |
  tr -d '[:space:]'
)"

USER_COUNT="$(
  kubectl exec \
    -n "$NS" \
    "$POD" \
    -- mariadb \
      --host=127.0.0.1 \
      --protocol=TCP \
      --user=root \
      --password="$RESTORE_ROOT_PASSWORD" \
      --batch \
      --skip-column-names \
      --execute='
        SELECT COUNT(*)
        FROM nextcloud_restore.oc_users;
      ' |
  tr -d '[:space:]'
)"

FILECACHE_COUNT="$(
  kubectl exec \
    -n "$NS" \
    "$POD" \
    -- mariadb \
      --host=127.0.0.1 \
      --protocol=TCP \
      --user=root \
      --password="$RESTORE_ROOT_PASSWORD" \
      --batch \
      --skip-column-names \
      --execute='
        SELECT COUNT(*)
        FROM nextcloud_restore.oc_filecache;
      ' |
  tr -d '[:space:]'
)"

test "$TABLE_COUNT" -gt 100 \
  || fail "Muy pocas tablas restauradas: $TABLE_COUNT"

test "$FILECACHE_COUNT" -gt 0 \
  || fail "oc_filecache está vacío"

echo "Tablas:       $TABLE_COUNT"
echo "Usuarios:     $USER_COUNT"
echo "Filecache:    $FILECACHE_COUNT"

echo
echo "=================================================="
echo " NEXTCLOUD RESTORE DRY-RUN VALIDADO"
echo "=================================================="
echo
echo "Producción no fue modificada."
echo "Fin: $(date --iso-8601=seconds)"
