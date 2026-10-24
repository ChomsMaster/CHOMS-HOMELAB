#!/usr/bin/env bash

set -euo pipefail
umask 077

STAGING=/srv/storage/backups/homelab/nextcloud/staging
DAILY=/srv/storage/backups/homelab/nextcloud/daily
SNAPSHOT_SCRIPT=/usr/local/sbin/choms-nextcloud-reflink-snapshot.sh

ACTION="${1:-}"

case "$ACTION" in
  prepare)
    mkdir -p "$STAGING" "$DAILY"
    rm -f "$STAGING/mariadb-nextcloud.sql.gz"
    chown chomsmaster:chomsmaster "$STAGING"
    chmod 700 "$STAGING"
    ;;

  install-dump)
    SOURCE="${2:-}"

    test -n "$SOURCE"
    test -f "$SOURCE"

    mv "$SOURCE" "$STAGING/mariadb-nextcloud.sql.gz"

    chown root:root "$STAGING/mariadb-nextcloud.sql.gz"
    chmod 600 "$STAGING/mariadb-nextcloud.sql.gz"

    gzip -t "$STAGING/mariadb-nextcloud.sql.gz"
    ;;

  snapshot)
    STAMP="${2:-}"

    test "$STAMP" != ""
    [[ "$STAMP" =~ ^20[0-9]{6}-[0-9]{6}$ ]]

    "$SNAPSHOT_SCRIPT" "$STAMP"
    ;;

  validate)
    STAMP="${2:-}"
    DEST="$DAILY/$STAMP"

    [[ "$STAMP" =~ ^20[0-9]{6}-[0-9]{6}$ ]]
    test -d "$DEST"
    test -s "$DEST/mariadb-nextcloud.sql.gz"
    test -s "$DEST/files/config/config.php"
    test -f "$DEST/files/data/.ncdata"

    gzip -t "$DEST/mariadb-nextcloud.sql.gz"

    readlink -f "$DAILY/latest"
    ;;

  latest)
    DEST="$(readlink -f "$DAILY/latest")"

    test -n "$DEST"
    test -d "$DEST"
    test -s "$DEST/mariadb-nextcloud.sql.gz"
    test -s "$DEST/files/config/config.php"
    test -f "$DEST/files/data/.ncdata"

    gzip -t "$DEST/mariadb-nextcloud.sql.gz"

    echo "Latest: $DEST"
    du -sh "$DEST"
    find "$DEST"       -maxdepth 2       -mindepth 1       -printf '%M %u:%g %p
' |
    sort
    ;;

  restore-test)
    STAMP="${2:-latest}"
    RESTORE_ROOT=/srv/storage/backups/homelab/nextcloud/restore-tests

    if [ "$STAMP" = "latest" ]; then
      SOURCE="$(readlink -f "$DAILY/latest")"
      STAMP="$(basename "$SOURCE")"
    else
      [[ "$STAMP" =~ ^20[0-9]{6}-[0-9]{6}$ ]]
      SOURCE="$DAILY/$STAMP"
    fi

    test -d "$SOURCE"
    test -s "$SOURCE/mariadb-nextcloud.sql.gz"
    test -s "$SOURCE/files/config/config.php"
    test -f "$SOURCE/files/data/.ncdata"

    DEST="$RESTORE_ROOT/$STAMP"
    PARTIAL="$RESTORE_ROOT/.partial-$STAMP"

    mkdir -p "$RESTORE_ROOT"
    rm -rf "$PARTIAL" "$DEST"

    echo "Clonando snapshot para prueba..."
    echo "Origen:  $SOURCE"
    echo "Destino: $DEST"

    cp \
      -a \
      --reflink=always \
      "$SOURCE" \
      "$PARTIAL"

    gzip -t "$PARTIAL/mariadb-nextcloud.sql.gz"

    test -s "$PARTIAL/files/config/config.php"
    test -f "$PARTIAL/files/data/.ncdata"
    test -d "$PARTIAL/files/custom_apps"
    test -d "$PARTIAL/files/themes"

    (
      cd "$PARTIAL"
      sha256sum -c SHA256SUMS
    )

    mv "$PARTIAL" "$DEST"

    echo
    echo "RESTORE TEST DE ARCHIVOS VALIDADO"
    echo "Ruta: $DEST"
    du -sh "$DEST"
    ;;

  restore-test-clean)
    RESTORE_ROOT=/srv/storage/backups/homelab/nextcloud/restore-tests

    if [ -d "$RESTORE_ROOT" ]; then
      find "$RESTORE_ROOT" \
        -mindepth 1 \
        -maxdepth 1 \
        -type d \
        -print \
        -exec rm -rf {} +
    fi

    echo "Pruebas de restauración eliminadas."
    ;;

  export-dump)
    STAMP="${2:-latest}"
    EXPORT_PATH="${3:-}"

    test -n "$EXPORT_PATH"
    [[ "$EXPORT_PATH" =~ ^/tmp/mariadb-nextcloud-[0-9]{8}-[0-9]{6}\.sql\.gz$ ]]

    if [ "$STAMP" = "latest" ]; then
      SOURCE="$(readlink -f "$DAILY/latest")"
    else
      [[ "$STAMP" =~ ^20[0-9]{6}-[0-9]{6}$ ]]
      SOURCE="$DAILY/$STAMP"
    fi

    test -d "$SOURCE"
    test -s "$SOURCE/mariadb-nextcloud.sql.gz"

    gzip -t "$SOURCE/mariadb-nextcloud.sql.gz"

    cp \
      "$SOURCE/mariadb-nextcloud.sql.gz" \
      "$EXPORT_PATH"

    chown chomsmaster:chomsmaster "$EXPORT_PATH"
    chmod 600 "$EXPORT_PATH"

    echo "$EXPORT_PATH"
    ;;

  prepare-restore-config)
    STAMP="${2:-latest}"

    if [ "$STAMP" = "latest" ]; then
      SOURCE="$(readlink -f "$DAILY/latest")"
      STAMP="$(basename "$SOURCE")"
    else
      [[ "$STAMP" =~ ^20[0-9]{6}-[0-9]{6}$ ]]
    fi

    CONFIG="/srv/storage/backups/homelab/nextcloud/restore-tests/$STAMP/files/config/config.php"

    test -s "$CONFIG"

    cp -a "$CONFIG" "$CONFIG.before-restore-test"

    sed -i \
      -e 's/mariadb\.databases\.svc\.cluster\.local/mariadb/g' \
      -e 's/redis\.databases\.svc\.cluster\.local/redis/g' \
      "$CONFIG"

    echo "Configuración de restore preparada: $CONFIG"
    ;;

  *)
    echo "Uso: $0 {prepare|install-dump FILE|snapshot STAMP|validate STAMP|latest|restore-test [STAMP]|restore-test-clean|export-dump [STAMP] FILE|prepare-restore-config [STAMP]}"
    exit 2
    ;;
esac
