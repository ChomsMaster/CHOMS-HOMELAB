#!/usr/bin/env bash
set -euo pipefail
umask 077

ROOT=/srv/storage/backups/homelab/nextcloud

DAILY="$ROOT/daily"
WEEKLY="$ROOT/weekly"
MONTHLY="$ROOT/monthly"
YEARLY="$ROOT/yearly"

KEEP_DAILY=7
KEEP_WEEKLY=8
KEEP_MONTHLY=12
KEEP_YEARLY=5

mkdir -p "$DAILY" "$WEEKLY" "$MONTHLY" "$YEARLY"

LATEST="$(readlink -f "$DAILY/latest")"

test -n "$LATEST"
test -d "$LATEST"

STAMP="$(basename "$LATEST")"
BACKUP_DATE="${STAMP%%-*}"

YEAR="${BACKUP_DATE:0:4}"
MONTH="${BACKUP_DATE:4:2}"
DAY="${BACKUP_DATE:6:2}"

DATE_ISO="$YEAR-$MONTH-$DAY"

DOW="$(date -d "$DATE_ISO" +%u)"
DOM="$((10#$DAY))"
MON="$((10#$MONTH))"

clone_if_missing() {
  local source="$1"
  local destination_root="$2"
  local label="$3"
  local destination="$destination_root/$STAMP"
  local partial="$destination_root/.partial-$STAMP"

  if [ -d "$destination" ]; then
    echo "$label: $STAMP ya existe."
    ln -sfn "$STAMP" "$destination_root/latest"
    return
  fi

  rm -rf "$partial"

  echo "$label: creando clon reflink..."

  cp \
    -a \
    --reflink=always \
    "$source" \
    "$partial"

  test -s "$partial/files/config/config.php"
  test -f "$partial/files/data/.ncdata"
  test -s "$partial/mariadb-nextcloud.sql.gz"

  gzip -t "$partial/mariadb-nextcloud.sql.gz"

  (
    cd "$partial"
    sha256sum -c SHA256SUMS
  )

  mv "$partial" "$destination"
  ln -sfn "$STAMP" "$destination_root/latest"

  echo "$label: promoción validada."
}

rotate() {
  local directory="$1"
  local keep="$2"
  local label="$3"

  mapfile -t snapshots < <(
    find "$directory" \
      -mindepth 1 \
      -maxdepth 1 \
      -type d \
      -name '20??????-??????' \
      -printf '%f\n' |
    sort -r
  )

  if [ "${#snapshots[@]}" -le "$keep" ]; then
    echo "$label: ${#snapshots[@]}/$keep."
    return
  fi

  for old in "${snapshots[@]:$keep}"; do
    echo "$label: eliminando $old"
    rm -rf "$directory/$old"
  done
}

echo "=================================================="
echo " CHOMS NEXTCLOUD GFS"
echo "=================================================="
echo "Snapshot diario: $LATEST"
echo "Fecha: $DATE_ISO"

if [ "$DOW" -eq 7 ]; then
  clone_if_missing "$LATEST" "$WEEKLY" "Weekly"
else
  echo "Weekly: no corresponde."
fi

if [ "$DOM" -eq 1 ]; then
  clone_if_missing "$LATEST" "$MONTHLY" "Monthly"
else
  echo "Monthly: no corresponde."
fi

if [ "$MON" -eq 1 ] && [ "$DOM" -eq 1 ]; then
  clone_if_missing "$LATEST" "$YEARLY" "Yearly"
else
  echo "Yearly: no corresponde."
fi

echo
echo "Aplicando retención..."

rotate "$DAILY" "$KEEP_DAILY" "Daily"
rotate "$WEEKLY" "$KEEP_WEEKLY" "Weekly"
rotate "$MONTHLY" "$KEEP_MONTHLY" "Monthly"
rotate "$YEARLY" "$KEEP_YEARLY" "Yearly"

echo
echo "========== INVENTARIO =========="

for tier in daily weekly monthly yearly; do
  count="$(
    find "$ROOT/$tier" \
      -mindepth 1 \
      -maxdepth 1 \
      -type d \
      -name '20??????-??????' |
    wc -l
  )"

  printf '%-8s %s\n' "$tier:" "$count"
done
