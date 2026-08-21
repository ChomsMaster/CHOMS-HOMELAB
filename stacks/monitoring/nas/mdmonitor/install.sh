#!/usr/bin/env bash

set -euo pipefail

MODE="${1:-plan}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$ROOT/systemd"
TARGET=/etc/systemd/system

UNITS=(
  mdmonitor.service
  mdmonitor-oneshot.service
)

fail() {
  echo "ERROR: $1" >&2
  exit 1
}

validate_override() {
  local unit="$1"
  local file="$SOURCE/$unit.d/override.conf"

  test -s "$file" || fail "Falta el drop-in de $unit"
  test "$(sed -n '/^\[Service\]$/p' "$file" | wc -l)" -eq 1 ||
    fail "Sección Service inválida en $unit"
  test "$(sed -n '/^ExecStart=$/p' "$file" | wc -l)" -eq 1 ||
    fail "Falta el reset de ExecStart en $unit"
  test "$(sed -n '/^ExecStart=./p' "$file" | wc -l)" -eq 1 ||
    fail "ExecStart inválido en $unit"
}

validate() {
  validate_override mdmonitor.service
  validate_override mdmonitor-oneshot.service

  grep -Fxq \
    'ExecStart=/usr/sbin/mdadm --monitor --scan --syslog' \
    "$SOURCE/mdmonitor.service.d/override.conf" ||
    fail "Argumentos inesperados en mdmonitor.service"
  grep -Fxq \
    'EnvironmentFile=' \
    "$SOURCE/mdmonitor-oneshot.service.d/override.conf" ||
    fail "Falta el reset de EnvironmentFile en mdmonitor-oneshot.service"
  grep -Fxq \
    'EnvironmentFile=-/etc/default/mdadm' \
    "$SOURCE/mdmonitor-oneshot.service.d/override.conf" ||
    fail "EnvironmentFile inesperado en mdmonitor-oneshot.service"
  grep -Fxq \
    'ExecStart=sh -c '\''[ "$AUTOSCAN" != "true" ] || /usr/sbin/mdadm --monitor --oneshot --scan --syslog'\''' \
    "$SOURCE/mdmonitor-oneshot.service.d/override.conf" ||
    fail "Argumentos inesperados en mdmonitor-oneshot.service"

  echo "Validación declarativa de mdmonitor completada."
}

show_plan() {
  local unit
  for unit in "${UNITS[@]}"; do
    echo "  $SOURCE/$unit.d/override.conf -> $TARGET/$unit.d/override.conf"
  done
  echo "  systemctl daemon-reload"
  echo "  systemctl restart mdmonitor.service"
  echo "  systemctl start mdmonitor-oneshot.service"
}

rollback() {
  trap - ERR
  set +e
  rm -f \
    "$TARGET/mdmonitor.service.d/override.conf" \
    "$TARGET/mdmonitor-oneshot.service.d/override.conf"
  rmdir \
    "$TARGET/mdmonitor.service.d" \
    "$TARGET/mdmonitor-oneshot.service.d" 2>/dev/null
  systemctl daemon-reload
  systemctl restart mdmonitor.service
  echo "ERROR: aplicación fallida; se restauraron las unidades vendor" >&2
}

is_previous_oneshot_override() {
  local file="$TARGET/mdmonitor-oneshot.service.d/override.conf"

  test -f "$file" || return 1
  test "$(wc -l < "$file")" -eq 3 || return 1
  grep -Fxq '[Service]' "$file" || return 1
  grep -Fxq 'ExecStart=' "$file" || return 1
  grep -Fxq \
    'ExecStart=/usr/sbin/mdadm --monitor --oneshot --scan --syslog' \
    "$file"
}

rollback_reconcile() {
  trap - ERR
  set +e
  install -o root -g root -m 0644 \
    "$RECONCILE_BACKUP" \
    "$TARGET/mdmonitor-oneshot.service.d/override.conf"
  systemctl daemon-reload
  systemctl start mdmonitor-oneshot.service
  rm -rf "$RECONCILE_DIR"
  echo "ERROR: reconciliación fallida; se restauró el override anterior" >&2
}

case "$MODE" in
  plan)
    validate
    show_plan
    echo "PLAN VALIDADO. No se modificó el sistema."
    ;;
  apply)
    test "$(id -u)" -eq 0 || fail "El modo apply debe ejecutarse como root"
    validate

    for unit in "${UNITS[@]}"; do
      test ! -e "$TARGET/$unit.d/override.conf" ||
        fail "Ya existe un override para $unit; no se sobrescribe"
    done

    trap rollback ERR
    for unit in "${UNITS[@]}"; do
      install -d -o root -g root -m 0755 "$TARGET/$unit.d"
      install -o root -g root -m 0644 \
        "$SOURCE/$unit.d/override.conf" \
        "$TARGET/$unit.d/override.conf"
    done

    systemctl daemon-reload
    systemctl restart mdmonitor.service
    systemctl start mdmonitor-oneshot.service
    trap - ERR
    ;;
  reconcile-oneshot)
    test "$(id -u)" -eq 0 ||
      fail "El modo reconcile-oneshot debe ejecutarse como root"
    validate
    is_previous_oneshot_override ||
      fail "El override instalado no coincide exactamente con la versión esperada"

    RECONCILE_DIR="$(mktemp -d /run/choms-mdmonitor-reconcile.XXXXXX)"
    RECONCILE_BACKUP="$RECONCILE_DIR/override.conf"
    install -o root -g root -m 0600 \
      "$TARGET/mdmonitor-oneshot.service.d/override.conf" \
      "$RECONCILE_BACKUP"
    trap rollback_reconcile ERR
    install -o root -g root -m 0644 \
      "$SOURCE/mdmonitor-oneshot.service.d/override.conf" \
      "$TARGET/mdmonitor-oneshot.service.d/override.conf"
    systemctl daemon-reload
    systemctl start mdmonitor-oneshot.service
    trap - ERR
    rm -rf "$RECONCILE_DIR"
    ;;
  *)
    fail "Uso: $0 {plan|apply|reconcile-oneshot}"
    ;;
esac
