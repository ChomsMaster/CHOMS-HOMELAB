#!/usr/bin/env bash

set -euo pipefail
umask 077

BACKUP_ROOT=/data/backups/kubernetes
RETENTION_DAYS=14

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$STAMP"
TEMP_DIR="$BACKUP_ROOT/.tmp-$STAMP"

cleanup() {
  rm -rf "$TEMP_DIR"
}

trap cleanup EXIT

fail() {
  echo "ERROR: $1" >&2
  exit 1
}

mkdir -p "$BACKUP_ROOT"
mkdir -p "$TEMP_DIR"

kubectl rollout status deployment/postgres \
  -n databases \
  --timeout=180s

kubectl rollout status deployment/mariadb \
  -n databases \
  --timeout=180s

kubectl rollout status deployment/redis \
  -n databases \
  --timeout=180s

POSTGRES_POD="$(
  kubectl get pod \
    -n databases \
    -l app=postgres \
    -o jsonpath='{.items[0].metadata.name}'
)"

MARIADB_POD="$(
  kubectl get pod \
    -n databases \
    -l app=mariadb \
    -o jsonpath='{.items[0].metadata.name}'
)"

REDIS_POD="$(
  kubectl get pod \
    -n databases \
    -l app=redis \
    -o jsonpath='{.items[0].metadata.name}'
)"

POSTGRES_USER="$(
  kubectl get secret postgres-secret \
    -n databases \
    -o jsonpath='{.data.POSTGRES_USER}' |
  base64 -d
)"

POSTGRES_DB="$(
  kubectl get secret postgres-secret \
    -n databases \
    -o jsonpath='{.data.POSTGRES_DB}' |
  base64 -d
)"

MARIADB_PASSWORD="$(
  kubectl get secret mariadb-secret \
    -n apps \
    -o jsonpath='{.data.MARIADB_PASSWORD}' |
  base64 -d
)"

echo "Creando dump PostgreSQL..."

kubectl exec \
  -n databases \
  "$POSTGRES_POD" \
  -- pg_dump \
    --username="$POSTGRES_USER" \
    --dbname="$POSTGRES_DB" \
    --format=custom \
    --no-owner \
    --no-privileges \
  > "$TEMP_DIR/postgres-$POSTGRES_DB.dump"

test -s "$TEMP_DIR/postgres-$POSTGRES_DB.dump" \
  || fail "Dump PostgreSQL vacío"

kubectl exec \
  -i \
  -n databases \
  "$POSTGRES_POD" \
  -- pg_restore --list \
  < "$TEMP_DIR/postgres-$POSTGRES_DB.dump" \
  > "$TEMP_DIR/postgres-contents.txt"

test -s "$TEMP_DIR/postgres-contents.txt" \
  || fail "No se pudo validar PostgreSQL"

echo "Creando dump MariaDB..."

kubectl exec \
  -n databases \
  "$MARIADB_POD" \
  -- env MYSQL_PWD="$MARIADB_PASSWORD" \
    mariadb-dump \
      --user=nextcloud \
      --single-transaction \
      --quick \
      --routines \
      --triggers \
      --events \
      --databases nextcloud \
  > "$TEMP_DIR/mariadb-nextcloud.sql"

grep -q 'CREATE TABLE' \
  "$TEMP_DIR/mariadb-nextcloud.sql" \
  || fail "Dump MariaDB sin tablas"

gzip -9 "$TEMP_DIR/mariadb-nextcloud.sql"
gzip -t "$TEMP_DIR/mariadb-nextcloud.sql.gz"

echo "Respaldando Redis..."

kubectl exec \
  -n databases \
  "$REDIS_POD" \
  -- sh -euc '
    redis-cli \
      --no-auth-warning \
      -a "$REDIS_PASSWORD" \
      SAVE >/dev/null

    test -s /data/dump.rdb
    redis-check-rdb /data/dump.rdb
  ' \
  > "$TEMP_DIR/redis-validation.txt"

kubectl exec \
  -n databases \
  "$REDIS_POD" \
  -- cat /data/dump.rdb \
  > "$TEMP_DIR/redis-dump.rdb"

test -s "$TEMP_DIR/redis-dump.rdb" \
  || fail "Dump Redis vacío"

test -s "$TEMP_DIR/redis-validation.txt" \
  || fail "No se pudo validar Redis"

echo "Exportando inventario runtime sin objetos Secret..."

kubectl get \
  namespaces,deployments,statefulsets,daemonsets,services,persistentvolumeclaims \
  -A \
  -o yaml \
  > "$TEMP_DIR/kubernetes-resources.yaml"

kubectl get gateways,httproutes \
  -A \
  -o yaml \
  > "$TEMP_DIR/kubernetes-routes.yaml"

kubectl get ipaddresspools,l2advertisements \
  -A \
  -o yaml \
  > "$TEMP_DIR/metallb-resources.yaml"

kubectl get certificates \
  -A \
  -o yaml \
  > "$TEMP_DIR/certificates.yaml"

kubectl get clusterissuers \
  -o yaml \
  > "$TEMP_DIR/clusterissuers.yaml"

kubectl get nodes \
  -o wide \
  > "$TEMP_DIR/nodes.txt"

kubectl version \
  -o yaml \
  > "$TEMP_DIR/kubernetes-version.yaml"

helm list \
  -A \
  -o json \
  > "$TEMP_DIR/helm-releases.json"

for inventory in \
  kubernetes-resources.yaml \
  kubernetes-routes.yaml \
  metallb-resources.yaml \
  certificates.yaml \
  clusterissuers.yaml \
  nodes.txt \
  kubernetes-version.yaml \
  helm-releases.json
do
  test -s "$TEMP_DIR/$inventory" \
    || fail "Inventario vacío: $inventory"
done

tar \
  -C "$TEMP_DIR" \
  -czf "$TEMP_DIR/kubernetes-runtime.tgz" \
  kubernetes-resources.yaml \
  kubernetes-routes.yaml \
  metallb-resources.yaml \
  certificates.yaml \
  clusterissuers.yaml \
  nodes.txt \
  kubernetes-version.yaml \
  helm-releases.json

tar -tzf "$TEMP_DIR/kubernetes-runtime.tgz" \
  >/dev/null

rm -f \
  "$TEMP_DIR/kubernetes-resources.yaml" \
  "$TEMP_DIR/kubernetes-routes.yaml" \
  "$TEMP_DIR/metallb-resources.yaml" \
  "$TEMP_DIR/certificates.yaml" \
  "$TEMP_DIR/clusterissuers.yaml" \
  "$TEMP_DIR/nodes.txt" \
  "$TEMP_DIR/kubernetes-version.yaml" \
  "$TEMP_DIR/helm-releases.json"

echo "Comprobando configuración no sensible de K3s..."

K3S_CONFIG_INCLUDED=no

if [ -r /etc/rancher/k3s/config.yaml ]; then
  tar \
    -C /etc \
    -czf "$TEMP_DIR/k3s-config.tgz" \
    rancher/k3s/config.yaml

  tar -tzf "$TEMP_DIR/k3s-config.tgz" >/dev/null
  K3S_CONFIG_INCLUDED=yes
else
  echo "K3s config no legible; no se crea un archivo vacío."
fi

cat > "$TEMP_DIR/metadata.txt" <<META
Created: $(date --iso-8601=seconds)
Host: $(hostname)
PostgreSQL database: $POSTGRES_DB
MariaDB database: nextcloud
Kubernetes Secret objects included: no
K3s config included: $K3S_CONFIG_INCLUDED
Retention days: $RETENTION_DAYS
META

(
  cd "$TEMP_DIR"

  find . \
    -maxdepth 1 \
    -type f \
    ! -name SHA256SUMS \
    -printf '%f\0' |
  sort -z |
  xargs -0 sha256sum \
    > SHA256SUMS

  sha256sum -c SHA256SUMS
)

mv "$TEMP_DIR" "$BACKUP_DIR"
trap - EXIT

echo "Backup creado:"
echo "  $BACKUP_DIR"

find "$BACKUP_ROOT" \
  -mindepth 1 \
  -maxdepth 1 \
  -type d \
  -name '20??????-??????' \
  -mtime +"$RETENTION_DAYS" \
  -print \
  -exec rm -rf {} +

echo "Backups disponibles:"
find "$BACKUP_ROOT" \
  -mindepth 1 \
  -maxdepth 1 \
  -type d \
  -name '20??????-??????' \
  -printf '%TY-%Tm-%Td %TH:%TM  %p\n' |
sort -r
