#!/usr/bin/env bash

set -euo pipefail

MODE="${1:-plan}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_SOURCE="$ROOT/scripts"
UNIT_SOURCE="$ROOT/systemd"

SCRIPTS=(
  choms-kubernetes-backup.sh
  choms-backup-nas-sync.sh
  choms-backup-gfs-retention.sh
  choms-nextcloud-data-backup.sh
  choms-nextcloud-restore-test.sh
)

UNITS=(
  choms-kubernetes-backup.service
  choms-kubernetes-backup.timer
  choms-backup-nas-sync.service
  choms-backup-nas-sync.timer
  choms-backup-gfs-retention.service
  choms-backup-gfs-retention.timer
  choms-nextcloud-data-backup.service
  choms-nextcloud-data-backup.timer
)

TIMERS=(
  choms-kubernetes-backup.timer
  choms-backup-nas-sync.timer
  choms-backup-gfs-retention.timer
  choms-nextcloud-data-backup.timer
)

fail() {
  echo "ERROR: $1" >&2
  exit 1
}

validate() {
  for script in "${SCRIPTS[@]}"; do
    test -s "$SCRIPT_SOURCE/$script" ||
      fail "Falta el script $script"
    bash -n "$SCRIPT_SOURCE/$script"
  done

  for unit in "${UNITS[@]}"; do
    test -s "$UNIT_SOURCE/$unit" ||
      fail "Falta la unidad $unit"
  done

  command -v kubectl >/dev/null ||
    fail "kubectl no está instalado"
  command -v helm >/dev/null ||
    fail "Helm no está instalado"
  command -v openssl >/dev/null ||
    fail "OpenSSL no está instalado"

  findmnt -T /data/backups >/dev/null ||
    fail "/data/backups no tiene filesystem accesible"
  findmnt -T /mnt/choms-backups -t nfs,nfs4 >/dev/null ||
    fail "/mnt/choms-backups no está montado mediante NFS"
  findmnt -T /mnt/choms-storage -t nfs,nfs4 >/dev/null ||
    fail "/mnt/choms-storage no está montado mediante NFS"

  test -r /home/chomsmaster/.ssh/choms_nas_backup ||
    fail "Falta la clave SSH del backup del NAS"

  echo "Validación de Node-01 completada."
}

show_plan() {
  echo "Scripts:"
  for script in "${SCRIPTS[@]}"; do
    echo "  $SCRIPT_SOURCE/$script -> /usr/local/sbin/$script"
  done

  echo
  echo "Unidades:"
  for unit in "${UNITS[@]}"; do
    echo "  $UNIT_SOURCE/$unit -> /etc/systemd/system/$unit"
  done

  echo
  echo "Timers que serán habilitados:"
  printf '  %s\n' "${TIMERS[@]}"
}

case "$MODE" in
  plan)
    validate
    show_plan
    echo
    echo "PLAN VALIDADO. No se modificó el sistema."
    ;;

  apply)
    test "$(id -u)" -eq 0 ||
      fail "El modo apply debe ejecutarse como root"

    validate

    for script in "${SCRIPTS[@]}"; do
      install \
        -o root \
        -g root \
        -m 0755 \
        "$SCRIPT_SOURCE/$script" \
        "/usr/local/sbin/$script"
    done

    for unit in "${UNITS[@]}"; do
      install \
        -o root \
        -g root \
        -m 0644 \
        "$UNIT_SOURCE/$unit" \
        "/etc/systemd/system/$unit"
    done

    systemctl daemon-reload
    systemctl enable --now "${TIMERS[@]}"

    echo
    echo "INSTALACIÓN DE NODE-01 COMPLETADA."
    systemctl list-timers --all --no-pager |
      grep -E 'choms-(kubernetes-backup|backup-nas-sync|backup-gfs-retention|nextcloud-data-backup)'
    ;;

  *)
    fail "Uso: $0 {plan|apply}"
    ;;
esac
