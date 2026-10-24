#!/usr/bin/env bash

set -euo pipefail

MODE="${1:-plan}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_SOURCE="$ROOT/scripts"
UNIT_SOURCE="$ROOT/systemd"
SUDOERS_SOURCE="$ROOT/sudoers/choms-nextcloud-backup"
VISUDO=/usr/sbin/visudo

SCRIPTS=(
  choms-nextcloud-backup-control.sh
  choms-nextcloud-gfs.sh
  choms-nextcloud-reflink-snapshot.sh
)

UNITS=(
  choms-nextcloud-gfs.service
  choms-nextcloud-gfs.timer
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

  test -s "$SUDOERS_SOURCE" ||
    fail "Falta la política sudoers"

  test -x "$VISUDO" ||
    fail "visudo no está instalado en $VISUDO"

  "$VISUDO" -cf "$SUDOERS_SOURCE"

  test "$(findmnt -no FSTYPE -T /srv/storage)" = "xfs" ||
    fail "/srv/storage no está montado en XFS"

  test -d /srv/storage/kubernetes ||
    fail "No existe /srv/storage/kubernetes"

  echo "Validación del NAS completada."
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
  echo "Sudoers:"
  echo "  $SUDOERS_SOURCE -> /etc/sudoers.d/choms-nextcloud-backup"
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

    install \
      -o root \
      -g root \
      -m 0440 \
      "$SUDOERS_SOURCE" \
      /etc/sudoers.d/choms-nextcloud-backup

    "$VISUDO" -cf /etc/sudoers.d/choms-nextcloud-backup
    systemctl daemon-reload
    systemctl enable --now choms-nextcloud-gfs.timer

    echo
    echo "INSTALACIÓN DEL NAS COMPLETADA."
    systemctl status \
      choms-nextcloud-gfs.timer \
      --no-pager \
      --lines=10
    ;;

  *)
    fail "Uso: $0 {plan|apply}"
    ;;
esac
