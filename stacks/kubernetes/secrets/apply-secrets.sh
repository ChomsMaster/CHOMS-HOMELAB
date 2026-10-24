#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")"
  pwd
)"

ENV_FILE="${SCRIPT_DIR}/secrets.env"
KUBE_HOST="${KUBE_HOST:-chomsmaster@192.168.1.138}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: missing ${ENV_FILE}"
  echo "Create it from secrets.env.example"
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

required_vars=(
  CHOMS_CONTROLLER_APP_NAME
  CHOMS_CONTROLLER_APP_VERSION
  CHOMS_CONTROLLER_DATABASE_URL
  NEXTCLOUD_MARIADB_PASSWORD
  NEXTCLOUD_REDIS_PASSWORD
  MARIADB_PASSWORD
  MARIADB_ROOT_PASSWORD
  POSTGRES_DB
  POSTGRES_USER
  POSTGRES_PASSWORD
  REDIS_PASSWORD
  GRAFANA_ADMIN_USER
  GRAFANA_ADMIN_PASSWORD
  AUTHELIA_JWT_SECRET
  AUTHELIA_SESSION_SECRET
  AUTHELIA_STORAGE_ENCRYPTION_KEY
  AUTHELIA_REDIS_PASSWORD
)

for var in "${required_vars[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    echo "ERROR: ${var} is empty"
    exit 1
  fi
done

apply_secret() {
  local namespace="$1"
  local name="$2"
  shift 2

  echo "APPLY ${namespace}/${name}"

  python3 - "$namespace" "$name" "$@" <<'PY' |
import base64
import json
import os
import sys

namespace = sys.argv[1]
name = sys.argv[2]
pairs = sys.argv[3:]

data = {}

for pair in pairs:
    key, env_name = pair.split("=", 1)
    value = os.environ[env_name].encode()
    data[key] = base64.b64encode(value).decode()

doc = {
    "apiVersion": "v1",
    "kind": "Secret",
    "metadata": {
        "name": name,
        "namespace": namespace,
    },
    "type": "Opaque",
    "data": data,
}

json.dump(doc, sys.stdout)
PY
  ssh "$KUBE_HOST" 'kubectl apply -f -'
}

apply_secret apps choms-controller-secret \
  APP_NAME=CHOMS_CONTROLLER_APP_NAME \
  APP_VERSION=CHOMS_CONTROLLER_APP_VERSION \
  DATABASE_URL=CHOMS_CONTROLLER_DATABASE_URL

apply_secret apps mariadb-secret \
  MARIADB_PASSWORD=NEXTCLOUD_MARIADB_PASSWORD

apply_secret apps redis-secret \
  REDIS_PASSWORD=NEXTCLOUD_REDIS_PASSWORD

apply_secret databases mariadb-secret \
  MARIADB_PASSWORD=MARIADB_PASSWORD \
  MARIADB_ROOT_PASSWORD=MARIADB_ROOT_PASSWORD

apply_secret databases postgres-secret \
  POSTGRES_DB=POSTGRES_DB \
  POSTGRES_USER=POSTGRES_USER \
  POSTGRES_PASSWORD=POSTGRES_PASSWORD

apply_secret databases redis-secret \
  REDIS_PASSWORD=REDIS_PASSWORD

apply_secret monitoring grafana-admin \
  admin-user=GRAFANA_ADMIN_USER \
  admin-password=GRAFANA_ADMIN_PASSWORD

apply_secret security authelia-secrets \
  jwt_secret=AUTHELIA_JWT_SECRET \
  session_secret=AUTHELIA_SESSION_SECRET \
  storage_encryption_key=AUTHELIA_STORAGE_ENCRYPTION_KEY

apply_secret security authelia-redis-secret \
  redis_password=AUTHELIA_REDIS_PASSWORD

echo
echo "Secrets bootstrap completed."
