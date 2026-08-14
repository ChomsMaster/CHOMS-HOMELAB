#!/usr/bin/env bash
set -euo pipefail
umask 077

SOURCE_ROOT=/srv/storage/kubernetes
BACKUP_ROOT=/srv/storage/backups/homelab/nextcloud
DAILY="$BACKUP_ROOT/daily"
STAGING="$BACKUP_ROOT/staging"

STAMP="${1:-$(date +%Y%m%d-%H%M%S)}"
PARTIAL="$DAILY/.partial-$STAMP"
FINAL="$DAILY/$STAMP"
KEEP_DAILY=7

PVC_DIR="$(
  find "$SOURCE_ROOT" \
    -mindepth 1 \
    -maxdepth 1 \
    -type d \
    -name 'apps-nextcloud-storage-pvc-*' \
    -print \
    -quit
)"

test -n "$PVC_DIR" || {
  echo "ERROR: PVC de Nextcloud no encontrado"
  exit 1
}

test -s "$PVC_DIR/config/config.php"
test -f "$PVC_DIR/data/.ncdata"
test ! -e "$FINAL"

mkdir -p "$DAILY" "$STAGING"
rm -rf "$PARTIAL"
mkdir -p "$PARTIAL/files"

cleanup() {
  status=$?

  if [ "$status" -ne 0 ]; then
    echo "ERROR: snapshot incompleto:"
    echo "  $PARTIAL"
  fi
}

trap cleanup EXIT

echo "Origen:"
echo "  $PVC_DIR"
echo
echo "Destino:"
echo "  $FINAL"

for item in data config custom_apps themes; do
  test -d "$PVC_DIR/$item"

  echo "Clonando $item..."

  cp \
    -a \
    --reflink=always \
    "$PVC_DIR/$item" \
    "$PARTIAL/files/"
done

if [ -s "$STAGING/mariadb-nextcloud.sql.gz" ]; then
  cp -a \
    "$STAGING/mariadb-nextcloud.sql.gz" \
    "$PARTIAL/"

  gzip -t "$PARTIAL/mariadb-nextcloud.sql.gz"
else
  echo "AVISO: snapshot sin dump de MariaDB."
fi

test -s "$PARTIAL/files/config/config.php"
test -f "$PARTIAL/files/data/.ncdata"

cat > "$PARTIAL/metadata.txt" <<META
Created: $(date --iso-8601=seconds)
Host: $(hostname)
Source: $PVC_DIR
Filesystem: $(findmnt -no FSTYPE -T "$PVC_DIR")
Reflink: enabled
MariaDB dump: $(test -s "$PARTIAL/mariadb-nextcloud.sql.gz" && echo yes || echo no)
META

(
  cd "$PARTIAL"

  find . \
    -maxdepth 1 \
    -type f \
    ! -name SHA256SUMS \
    -printf '%f\0' |
  sort -z |
  xargs -0 -r sha256sum \
    > SHA256SUMS

  if [ -s SHA256SUMS ]; then
    sha256sum -c SHA256SUMS
  fi
)

mv "$PARTIAL" "$FINAL"
ln -sfn "$STAMP" "$DAILY/latest"

mapfile -t snapshots < <(
  find "$DAILY" \
    -mindepth 1 \
    -maxdepth 1 \
    -type d \
    -name '20??????-??????' \
    -printf '%f\n' |
  sort -r
)

if [ "${#snapshots[@]}" -gt "$KEEP_DAILY" ]; then
  for old in "${snapshots[@]:$KEEP_DAILY}"; do
    echo "Eliminando snapshot antiguo: $old"
    rm -rf "$DAILY/$old"
  done
fi

trap - EXIT

echo
echo "Snapshot creado:"
echo "  $FINAL"
