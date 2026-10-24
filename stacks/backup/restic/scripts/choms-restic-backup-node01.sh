#!/usr/bin/env bash
# shellcheck disable=SC1091
export CHOMS_RESTIC_SFTP_KEY=/root/.ssh/choms-restic-node01
source /usr/local/lib/choms-restic-common.sh
export RESTIC_REPOSITORY='sftp:choms-restic@192.168.1.134:/choms-platforms-restic'
export RESTIC_HOST='choms-node-01'
start=$(date +%s)
PACKAGE_VALID=0 PACKAGE_TIMESTAMP=0 PACKAGE_AGE=0
bytes=0 work=
cleanup(){ rc=$?; [[ -z "$work" ]] || rm -rf -- "$work"; [ "$rc" -eq 0 ] || publish_metric 0 "$(( $(date +%s)-start ))" "$bytes" 0; exit "$rc"; }; trap cleanup EXIT; trap 'exit 130' INT; trap 'exit 143' TERM; trap 'exit 129' HUP
# Plaintext staging must remain on RAM-backed /run, with private permissions.
test "$(stat -f -c %T /run)" = tmpfs
umask 077
work=$(mktemp -d /run/choms-restic.XXXXXX)
test "$(stat -c '%u:%a' "$work")" = 0:700
select_database_package /data/backups/kubernetes "$start" "$work/package"
test -f /var/lib/rancher/k3s/server/db/state.db
test ! -e /var/lib/rancher/k3s/server/db/etcd/member
if test -f /etc/rancher/k3s/config.yaml; then
  ! grep -Eq '^[[:space:]]*(datastore-endpoint|cluster-init):' /etc/rancher/k3s/config.yaml
fi
python3 - "$work/state.db" <<'PY'
import sqlite3, sys
source=sqlite3.connect('file:/var/lib/rancher/k3s/server/db/state.db?mode=ro', uri=True)
destination=sqlite3.connect(sys.argv[1]); source.backup(destination)
assert destination.execute('PRAGMA integrity_check').fetchone() == ('ok',)
destination.close(); source.close()
PY
k3s_paths=("$work/state.db" /var/lib/rancher/k3s/server/tls /var/lib/rancher/k3s/server/token /etc/rancher/k3s /etc/choms-backup/recovery-sample.txt)
platform_paths=("$DATABASE_PACKAGE" /mnt/choms-storage/kubernetes/apps-portainer-data-pvc-50b7d8c5-8cc1-46d5-9e0f-35407a4e3dfc /mnt/choms-storage/kubernetes/apps-uptime-kuma-data-pvc-db048d0d-5ab9-4cb8-b28b-eccb8b980dc1 /mnt/choms-storage/kubernetes/security-authelia-data-pvc-7e6356ce-8166-4ac7-a829-9a0f2283e9ed /mnt/choms-storage/kubernetes/monitoring-choms-monitoring-grafana-pvc-233ae869-8985-4ec5-8efd-49c90251df66 /mnt/choms-storage/docker/filebrowser/config /mnt/choms-storage/docker/filebrowser/database /mnt/choms-backups/scrutiny/logical/daily/latest/)
kubectl get secret -A -o json | jq '{apiVersion,kind,items:[.items[]|select(.type != "kubernetes.io/service-account-token" and .type != "helm.sh/release.v1")|del(.metadata.managedFields,.metadata.resourceVersion,.metadata.uid,.metadata.creationTimestamp)]}' >"$work/recovery-secrets.json"
nc=/mnt/choms-storage/kubernetes/apps-nextcloud-storage-pvc-2fbee8b2-917a-43ea-89e4-cf8d703ae466
find "$nc" -xdev -mindepth 1 -maxdepth 1 -type f -print >"$work/nextcloud-root-files"
printf '%s\n' "$nc/config" "$nc/custom_apps" "$nc/themes" >>"$work/nextcloud-root-files"
! grep -q '/data\(/\|$\)' "$work/nextcloud-root-files"
mapfile -t nextcloud_paths <"$work/nextcloud-root-files"
measurement=()
for path in "${k3s_paths[@]}" "${nextcloud_paths[@]}" "$work/recovery-secrets.json"; do
  measurement+=(none "$path")
done
for path in "${platform_paths[@]}"; do measurement+=(platform "$path"); done
bytes=$(measure_scope mixed "${measurement[@]}")
require_below_limit "$bytes"
# Recheck after preparation: a new/incomplete package must not be bypassed.
selected_package=${DATABASE_PACKAGE##*/}
select_database_package /data/backups/kubernetes "$(date +%s)" "" "$selected_package"
test "$selected_package" = "${DATABASE_PACKAGE##*/}"
# platform_paths still references the already validated private copy.
run_restic --retry-lock 20m backup --host "$RESTIC_HOST" --tag node-01 --tag type-k3s -- "${k3s_paths[@]}"
run_restic --retry-lock 20m backup --host "$RESTIC_HOST" --tag node-01 --tag type-secrets --stdin --stdin-filename recovery-secrets.json <"$work/recovery-secrets.json"
run_restic --retry-lock 20m backup --host "$RESTIC_HOST" --tag node-01 --tag type-platform --exclude '*/data/**' -- "${platform_paths[@]}"
run_restic --retry-lock 20m backup --host "$RESTIC_HOST" --tag node-01 --tag type-nextcloud --files-from "$work/nextcloud-root-files"
rm -rf -- "$work"
work=
publish_metric 1 "$(( $(date +%s)-start ))" "$bytes" "$(date +%s)"
trap - EXIT INT TERM HUP
