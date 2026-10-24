#!/usr/bin/env bash

set -euo pipefail
umask 077

NAS_ROOT=/mnt/choms-backups
BASE="$NAS_ROOT/kubernetes"

DAILY="$BASE/daily"
WEEKLY="$BASE/weekly"
MONTHLY="$BASE/monthly"
YEARLY="$BASE/yearly"
LOGS="$NAS_ROOT/logs"

KEEP_DAILY=7
KEEP_WEEKLY=8
KEEP_MONTHLY=12
KEEP_YEARLY=5

RUN_STAMP="$(date +%Y%m%d-%H%M%S)"
LOG_LOCAL="/tmp/choms-gfs-retention-$RUN_STAMP.log"

exec > >(tee -a "$LOG_LOCAL") 2>&1

fail() {
  echo "ERROR: $1"
  exit 1
}

rotate_directory() {
  local directory="$1"
  local keep="$2"
  local label="$3"

  mapfile -t entries < <(
    find "$directory" \
      -mindepth 1 \
      -maxdepth 1 \
      -type d \
      -name '20??????-??????' \
      -printf '%f\n' |
    sort -r
  )

  if [ "${#entries[@]}" -le "$keep" ]; then
    echo "$label: ${#entries[@]}/$keep; no se elimina nada."
    return
  fi

  for old in "${entries[@]:$keep}"; do
    echo "$label: eliminando $old"
    rm -rf "$directory/$old"
  done
}

promote_backup() {
  local source="$1"
  local destination_root="$2"
  local backup_name="$3"
  local label="$4"

  local destination="$destination_root/$backup_name"
  local temporary="$destination_root/.partial-$backup_name"

  if [ -d "$destination" ]; then
    echo "$label: $backup_name ya existe."
    ln -sfn "$backup_name" "$destination_root/latest"
    return
  fi

  rm -rf "$temporary"

  echo "$label: promocionando $backup_name mediante enlaces duros..."

  # Misma exportación y mismo filesystem del NAS:
  # cp -al reutiliza los datos y evita duplicarlos físicamente.
  cp -al "$source" "$temporary"

  (
    cd "$temporary"
    sha256sum -c SHA256SUMS
  )

  mv "$temporary" "$destination"
  ln -sfn "$backup_name" "$destination_root/latest"

  echo "$label: promoción validada."
}

echo "=================================================="
echo " CHOMS GFS RETENTION"
echo "=================================================="
echo "Inicio: $(date --iso-8601=seconds)"

findmnt -T "$NAS_ROOT" -t nfs,nfs4 >/dev/null \
  || fail "NAS no montado en $NAS_ROOT"

mkdir -p \
  "$DAILY" \
  "$WEEKLY" \
  "$MONTHLY" \
  "$YEARLY" \
  "$LOGS"

LATEST="$(
  find "$DAILY" \
    -mindepth 1 \
    -maxdepth 1 \
    -type d \
    -name '20??????-??????' \
    -printf '%f\n' |
  sort -r |
  head -1
)"

test -n "$LATEST" \
  || fail "No existe ningún backup diario"

SOURCE="$DAILY/$LATEST"

test -s "$SOURCE/SHA256SUMS" \
  || fail "$LATEST no contiene SHA256SUMS"

echo
echo "Backup fuente:"
echo "  $SOURCE"

(
  cd "$SOURCE"
  sha256sum -c SHA256SUMS
)

# El nombre contiene la fecha real del backup: YYYYMMDD-HHMMSS.
BACKUP_DATE="${LATEST%%-*}"

YEAR="${BACKUP_DATE:0:4}"
MONTH="${BACKUP_DATE:4:2}"
DAY="${BACKUP_DATE:6:2}"

DATE_ISO="$YEAR-$MONTH-$DAY"

DAY_OF_WEEK="$(date -d "$DATE_ISO" +%u)"
DAY_OF_MONTH="$((10#$DAY))"
MONTH_NUMBER="$((10#$MONTH))"

echo
echo "Fecha del backup: $DATE_ISO"
echo "Día de semana:    $DAY_OF_WEEK (7=domingo)"

# Weekly: todos los domingos.
if [ "$DAY_OF_WEEK" -eq 7 ]; then
  promote_backup "$SOURCE" "$WEEKLY" "$LATEST" "Weekly"
else
  echo "Weekly: hoy no corresponde."
fi

# Monthly: primer día de cada mes.
if [ "$DAY_OF_MONTH" -eq 1 ]; then
  promote_backup "$SOURCE" "$MONTHLY" "$LATEST" "Monthly"
else
  echo "Monthly: hoy no corresponde."
fi

# Yearly: 1 de enero.
if [ "$MONTH_NUMBER" -eq 1 ] && [ "$DAY_OF_MONTH" -eq 1 ]; then
  promote_backup "$SOURCE" "$YEARLY" "$LATEST" "Yearly"
else
  echo "Yearly: hoy no corresponde."
fi

echo
echo "Aplicando retención..."

rotate_directory "$DAILY" "$KEEP_DAILY" "Daily"
rotate_directory "$WEEKLY" "$KEEP_WEEKLY" "Weekly"
rotate_directory "$MONTHLY" "$KEEP_MONTHLY" "Monthly"
rotate_directory "$YEARLY" "$KEEP_YEARLY" "Yearly"

echo
echo "========== INVENTARIO =========="

for tier in daily weekly monthly yearly; do
  count="$(
    find "$BASE/$tier" \
      -mindepth 1 \
      -maxdepth 1 \
      -type d \
      -name '20??????-??????' |
    wc -l
  )"

  printf '%-8s %s copias\n' "$tier:" "$count"
done

echo
echo "=================================================="
echo " RETENCIÓN GFS COMPLETADA"
echo "=================================================="
echo "Fin: $(date --iso-8601=seconds)"

cp -f "$LOG_LOCAL" "$LOGS/gfs-$RUN_STAMP.log"
ln -sfn "gfs-$RUN_STAMP.log" "$LOGS/gfs-latest.log"

rm -f "$LOG_LOCAL"
