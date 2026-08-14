#!/usr/bin/env bash

set -euo pipefail
umask 077

LOCAL_ROOT=/data/backups/kubernetes
NAS_ROOT=/mnt/choms-backups
NAS_DAILY="$NAS_ROOT/kubernetes/daily"
NAS_LOGS="$NAS_ROOT/logs"

KEEP_DAILY=7

START_EPOCH="$(date +%s)"
RUN_STAMP="$(date +%Y%m%d-%H%M%S)"
LOG_LOCAL="/tmp/choms-backup-nas-sync-$RUN_STAMP.log"

exec > >(tee -a "$LOG_LOCAL") 2>&1

fail() {
  echo "ERROR: $1"
  exit 1
}

echo "=================================================="
echo " CHOMS BACKUP → NAS"
echo "=================================================="
echo "Inicio: $(date --iso-8601=seconds)"

test -d "$LOCAL_ROOT" \
  || fail "No existe el origen local: $LOCAL_ROOT"

findmnt -T "$NAS_ROOT" \
  -t nfs,nfs4 \
  >/dev/null \
  || fail "El NAS no está montado en $NAS_ROOT"

mkdir -p "$NAS_DAILY" "$NAS_LOGS"

LATEST="$(
  find "$LOCAL_ROOT" \
    -mindepth 1 \
    -maxdepth 1 \
    -type d \
    -name '20??????-??????' \
    -printf '%f\n' |
  sort -r |
  head -1
)"

test -n "$LATEST" \
  || fail "No existe ningún backup local válido"

SOURCE="$LOCAL_ROOT/$LATEST"
DESTINATION="$NAS_DAILY/$LATEST"
TEMP_DESTINATION="$NAS_DAILY/.partial-$LATEST"

test -s "$SOURCE/SHA256SUMS" \
  || fail "El backup local no contiene SHA256SUMS"

echo
echo "Backup seleccionado:"
echo "  $SOURCE"

echo
echo "Verificando origen..."

(
  cd "$SOURCE"
  sha256sum -c SHA256SUMS
)

rm -rf "$TEMP_DESTINATION"
mkdir -p "$TEMP_DESTINATION"

echo
echo "Copiando al NAS..."

rsync \
  -aH \
  --numeric-ids \
  --delete \
  --partial \
  "$SOURCE/" \
  "$TEMP_DESTINATION/"

echo
echo "Verificando copia del NAS..."

(
  cd "$TEMP_DESTINATION"
  sha256sum -c SHA256SUMS
)

# Publicación atómica: nunca dejamos un backup final incompleto.
if [ -d "$DESTINATION" ]; then
  echo "El backup ya existía. Sustituyendo por la copia verificada."
  rm -rf "$DESTINATION"
fi

mv "$TEMP_DESTINATION" "$DESTINATION"

ln -sfn "$LATEST" "$NAS_DAILY/latest"

echo
echo "Aplicando retención: conservar $KEEP_DAILY diarios..."

mapfile -t BACKUPS < <(
  find "$NAS_DAILY" \
    -mindepth 1 \
    -maxdepth 1 \
    -type d \
    -name '20??????-??????' \
    -printf '%f\n' |
  sort -r
)

if [ "${#BACKUPS[@]}" -gt "$KEEP_DAILY" ]; then
  for OLD in "${BACKUPS[@]:$KEEP_DAILY}"; do
    echo "Eliminando backup diario antiguo: $OLD"
    rm -rf "$NAS_DAILY/$OLD"
  done
fi

END_EPOCH="$(date +%s)"
DURATION="$((END_EPOCH - START_EPOCH))"
SIZE="$(du -sh "$DESTINATION" | awk '{print $1}')"

echo
echo "=================================================="
echo " SINCRONIZACIÓN COMPLETADA"
echo "=================================================="
echo "Backup:   $LATEST"
echo "Destino:  $DESTINATION"
echo "Tamaño:   $SIZE"
echo "Duración: ${DURATION}s"
echo "Fin:      $(date --iso-8601=seconds)"

cp -f "$LOG_LOCAL" "$NAS_LOGS/$RUN_STAMP.log"
ln -sfn "$RUN_STAMP.log" "$NAS_LOGS/latest.log"

rm -f "$LOG_LOCAL"
