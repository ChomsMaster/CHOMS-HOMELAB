#!/usr/bin/env bash

set -euo pipefail
set +x
umask 077

BACKUP_STAMP="${1:-}"
BACKUP_ROOT=/data/backups/kubernetes
MARIADB_IMAGE='docker.io/library/mariadb@sha256:efb4959ef2c835cd735dbc388eb9ad6aab0c78dd64febcd51bc17481111890c4'
POSTGRES_IMAGE='docker.io/library/postgres@sha256:a426e44bac0b759c95894d68e1a0ac03ecc20b619f498a91aae373bf06d8508d'
REDIS_IMAGE='docker.io/library/redis@sha256:595cc6f2bb3af6e03347b90deb6123c6aa2c81dea05ce08128de8a174b6ac67b'

test "$BACKUP_STAMP" = 20260830-031918 || {
  echo 'ERROR: this validation is authorized only for package 20260830-031918' >&2
  exit 1
}

BACKUP_DIR="$BACKUP_ROOT/$BACKUP_STAMP"
RUN_STAMP="$(date -u +%Y%m%d-%H%M%S)"
NAMESPACE="choms-recovery-test-20260830-${RUN_STAMP#*-}"
CONFIG_TMP="/tmp/$NAMESPACE-config"
CREATED=0
TEMP_PVS=''
MARIADB_PASSWORD="$(openssl rand -hex 24)"
POSTGRES_PASSWORD="$(openssl rand -hex 24)"
REDIS_PASSWORD="$(openssl rand -hex 24)"

cleanup() {
  status=$?
  rm -rf -- "$CONFIG_TMP"
  if [ "$CREATED" -eq 1 ]; then
    actual_temporary="$(kubectl get namespace "$NAMESPACE" -o jsonpath='{.metadata.labels.choms\.platform/temporary}' 2>/dev/null || true)"
    actual_purpose="$(kubectl get namespace "$NAMESPACE" -o jsonpath='{.metadata.labels.choms\.platform/purpose}' 2>/dev/null || true)"
    if [ "$actual_temporary" != true ] || [ "$actual_purpose" != recovery-test ]; then
      echo 'ERROR: cleanup guard refused namespace deletion' >&2
      exit 90
    fi
    echo "cleanup_namespace=$NAMESPACE"
    kubectl get all,pvc,secret,networkpolicy -n "$NAMESPACE" -o name | sort
    TEMP_PVS="$(kubectl get pvc -n "$NAMESPACE" -o jsonpath='{range .items[*]}{.spec.volumeName}{"\n"}{end}' | sed '/^$/d')"
    kubectl delete namespace "$NAMESPACE" --wait=true --timeout=5m >/dev/null
    test "$(kubectl get namespace "$NAMESPACE" --ignore-not-found -o name)" = ''
    while IFS= read -r pv; do
      [ -z "$pv" ] || test "$(kubectl get pv "$pv" --ignore-not-found -o name)" = ''
    done <<< "$TEMP_PVS"
    test "$(kubectl get pv -o jsonpath='{range .items[?(@.status.phase=="Released")]}{.metadata.name}{"\n"}{end}' | sed '/^$/d' | wc -l)" -eq "$RELEASED_PVS_BEFORE"
    test "$(kubectl get namespace -l choms.platform/purpose=recovery-test,choms.platform/temporary=true -o name | grep -Fx "namespace/$NAMESPACE" || true)" = ''
    echo 'cleanup=validated'
  fi
  exit "$status"
}
trap cleanup EXIT INT TERM

test -d "$BACKUP_DIR"
test -s "$BACKUP_DIR/SHA256SUMS"
test -s "$BACKUP_DIR/metadata.txt"
test -s "$BACKUP_DIR/mariadb-nextcloud.sql.gz"
test -s "$BACKUP_DIR/postgres-choms_platform.dump"
test -s "$BACKUP_DIR/redis-dump.rdb"
(cd "$BACKUP_DIR" && sha256sum -c SHA256SUMS >/dev/null)
available_kib="$(df -Pk / | awk 'NR==2 {print $4}')"
test "$available_kib" -ge 4194304

mkdir -m 0700 "$CONFIG_TMP"
tar -xzf "$BACKUP_DIR/kubernetes-runtime.tgz" -C "$CONFIG_TMP"
test -d "$CONFIG_TMP"
test "$(find "$CONFIG_TMP" -type f | wc -l)" -gt 0
test -z "$(find "$CONFIG_TMP" -perm /002 -print -quit)"
config_files="$(find "$CONFIG_TMP" -type f | wc -l)"

RELEASED_PVS_BEFORE="$(kubectl get pv -o jsonpath='{range .items[?(@.status.phase=="Released")]}{.metadata.name}{"\n"}{end}' | sed '/^$/d' | wc -l)"
production_before="$(kubectl get deployment -n databases mariadb postgres redis -o jsonpath='{range .items[*]}{.metadata.uid}{"="}{.metadata.resourceVersion}{"\n"}{end}' | sort)"
monitoring_before="$(kubectl get statefulset -n monitoring alertmanager-choms-monitoring-alertmanager prometheus-choms-monitoring-prometheus -o jsonpath='{range .items[*]}{.metadata.uid}{"="}{.metadata.resourceVersion}{"\n"}{end}' | sort)"
critical_before="$(kubectl get --raw '/api/v1/namespaces/monitoring/services/http:alertmanager-operated:9093/proxy/api/v2/alerts?active=true' | jq '[.[] | select(.labels.severity == "critical")] | length')"

kubectl create namespace "$NAMESPACE" >/dev/null
CREATED=1
kubectl label namespace "$NAMESPACE" \
  choms.platform/purpose=recovery-test \
  choms.platform/temporary=true >/dev/null

kubectl apply -f - >/dev/null <<YAML
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: default-deny, namespace: $NAMESPACE}
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
---
apiVersion: v1
kind: Secret
metadata: {name: recovery-credentials, namespace: $NAMESPACE}
type: Opaque
stringData:
  mariadb-password: "$MARIADB_PASSWORD"
  postgres-password: "$POSTGRES_PASSWORD"
  redis-password: "$REDIS_PASSWORD"
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata: {name: mariadb-data, namespace: $NAMESPACE}
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: local-path
  resources: {requests: {storage: 1Gi}}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata: {name: postgres-data, namespace: $NAMESPACE}
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: local-path
  resources: {requests: {storage: 512Mi}}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata: {name: redis-data, namespace: $NAMESPACE}
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: local-path
  resources: {requests: {storage: 256Mi}}
YAML

kubectl apply -f - >/dev/null <<YAML
apiVersion: v1
kind: Pod
metadata: {name: mariadb, namespace: $NAMESPACE, labels: {app: recovery-mariadb}}
spec:
  automountServiceAccountToken: false
  nodeSelector: {kubernetes.io/hostname: choms-node-01}
  tolerations: [{key: node-role.kubernetes.io/control-plane, operator: Exists, effect: NoSchedule}]
  containers:
  - name: mariadb
    image: $MARIADB_IMAGE
    env:
    - {name: MARIADB_ROOT_PASSWORD, valueFrom: {secretKeyRef: {name: recovery-credentials, key: mariadb-password}}}
    readinessProbe: {exec: {command: [healthcheck.sh, --connect, --innodb_initialized]}, periodSeconds: 2}
    resources: {requests: {cpu: 50m, memory: 128Mi}, limits: {cpu: 500m, memory: 512Mi}}
    volumeMounts: [{name: data, mountPath: /var/lib/mysql}]
  volumes: [{name: data, persistentVolumeClaim: {claimName: mariadb-data}}]
---
apiVersion: v1
kind: Pod
metadata: {name: postgres, namespace: $NAMESPACE, labels: {app: recovery-postgres}}
spec:
  automountServiceAccountToken: false
  nodeSelector: {kubernetes.io/hostname: choms-node-01}
  tolerations: [{key: node-role.kubernetes.io/control-plane, operator: Exists, effect: NoSchedule}]
  containers:
  - name: postgres
    image: $POSTGRES_IMAGE
    env:
    - {name: POSTGRES_PASSWORD, valueFrom: {secretKeyRef: {name: recovery-credentials, key: postgres-password}}}
    - {name: POSTGRES_DB, value: recovery_test}
    readinessProbe: {exec: {command: [pg_isready, -U, postgres, -d, recovery_test]}, periodSeconds: 2}
    resources: {requests: {cpu: 50m, memory: 128Mi}, limits: {cpu: 500m, memory: 512Mi}}
    volumeMounts: [{name: data, mountPath: /var/lib/postgresql/data}]
  volumes: [{name: data, persistentVolumeClaim: {claimName: postgres-data}}]
---
apiVersion: v1
kind: Pod
metadata: {name: redis, namespace: $NAMESPACE, labels: {app: recovery-redis}}
spec:
  automountServiceAccountToken: false
  nodeSelector: {kubernetes.io/hostname: choms-node-01}
  tolerations: [{key: node-role.kubernetes.io/control-plane, operator: Exists, effect: NoSchedule}]
  initContainers:
  - name: restore-rdb
    image: $REDIS_IMAGE
    command: [/bin/sh, -euc]
    args: ['cp /backup/redis-dump.rdb /data/dump.rdb; redis-check-rdb /data/dump.rdb >/dev/null']
    volumeMounts:
    - {name: backup, mountPath: /backup, readOnly: true}
    - {name: data, mountPath: /data}
  containers:
  - name: redis
    image: $REDIS_IMAGE
    command: [/bin/sh, -euc]
    args: ['exec redis-server --requirepass "$REDIS_PASSWORD" --dir /data --dbfilename dump.rdb']
    env:
    - {name: REDIS_PASSWORD, valueFrom: {secretKeyRef: {name: recovery-credentials, key: redis-password}}}
    readinessProbe: {exec: {command: [/bin/sh, -euc, 'REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli ping | grep -qx PONG']}, periodSeconds: 2}
    resources: {requests: {cpu: 25m, memory: 64Mi}, limits: {cpu: 250m, memory: 256Mi}}
    volumeMounts: [{name: data, mountPath: /data}]
  volumes:
  - {name: data, persistentVolumeClaim: {claimName: redis-data}}
  - {name: backup, hostPath: {path: $BACKUP_DIR, type: Directory}}
YAML

for component in mariadb postgres redis; do
  kubectl wait -n "$NAMESPACE" --for=condition=Ready "pod/$component" --timeout=5m >/dev/null
done

mariadb_start="$(date +%s%3N)"
gzip -dc "$BACKUP_DIR/mariadb-nextcloud.sql.gz" |
  kubectl exec -i -n "$NAMESPACE" mariadb -c mariadb -- sh -euc \
    'MYSQL_PWD="$MARIADB_ROOT_PASSWORD" mariadb -uroot' >/dev/null
mariadb_databases="$(kubectl exec -n "$NAMESPACE" mariadb -c mariadb -- sh -euc 'MYSQL_PWD="$MARIADB_ROOT_PASSWORD" mariadb -N -uroot -e "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name NOT IN (\"information_schema\",\"mysql\",\"performance_schema\",\"sys\")"')"
mariadb_tables="$(kubectl exec -n "$NAMESPACE" mariadb -c mariadb -- sh -euc 'MYSQL_PWD="$MARIADB_ROOT_PASSWORD" mariadb -N -uroot -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema NOT IN (\"information_schema\",\"mysql\",\"performance_schema\",\"sys\")"')"
test "$mariadb_databases" -gt 0
test "$mariadb_tables" -gt 0
kubectl exec -n "$NAMESPACE" mariadb -c mariadb -- sh -euc 'MYSQL_PWD="$MARIADB_ROOT_PASSWORD" mariadb -N -uroot nextcloud -e "CREATE TABLE recovery_probe(id INT PRIMARY KEY); INSERT INTO recovery_probe VALUES (1); SELECT COUNT(*) FROM recovery_probe; DROP TABLE recovery_probe" | grep -qx 1'
mariadb_end="$(date +%s%3N)"

postgres_start="$(date +%s%3N)"
kubectl exec -i -n "$NAMESPACE" postgres -c postgres -- pg_restore -U postgres -d recovery_test --no-owner --no-privileges < "$BACKUP_DIR/postgres-choms_platform.dump" >/dev/null
postgres_schemas="$(kubectl exec -n "$NAMESPACE" postgres -c postgres -- psql -U postgres -d recovery_test -Atc "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name NOT LIKE 'pg_%' AND schema_name <> 'information_schema'")"
postgres_tables="$(kubectl exec -n "$NAMESPACE" postgres -c postgres -- psql -U postgres -d recovery_test -Atc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')")"
kubectl exec -n "$NAMESPACE" postgres -c postgres -- psql -U postgres -d recovery_test -Atc 'CREATE TEMP TABLE recovery_probe(id integer); INSERT INTO recovery_probe VALUES (1); SELECT COUNT(*) FROM recovery_probe' | tail -1 | grep -qx 1
postgres_end="$(date +%s%3N)"

redis_start="$(date +%s%3N)"
redis_keys="$(kubectl exec -n "$NAMESPACE" redis -c redis -- sh -euc 'REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli --no-auth-warning DBSIZE')"
test "$redis_keys" -ge 0
kubectl exec -n "$NAMESPACE" redis -c redis -- sh -euc 'REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli --no-auth-warning SET choms:recovery:probe 1 >/dev/null; test "$(REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli --no-auth-warning EXISTS choms:recovery:probe)" = 1; REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli --no-auth-warning DEL choms:recovery:probe >/dev/null'
redis_end="$(date +%s%3N)"

test "$(kubectl get svc,ingress -n "$NAMESPACE" -o name | wc -l)" -eq 0
test "$(kubectl get httproute -n "$NAMESPACE" -o name 2>/dev/null | wc -l)" -eq 0
test "$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Running --no-headers | wc -l)" -eq 3
critical_after="$(kubectl get --raw '/api/v1/namespaces/monitoring/services/http:alertmanager-operated:9093/proxy/api/v2/alerts?active=true' | jq '[.[] | select(.labels.severity == "critical")] | length')"
test "$critical_after" -eq "$critical_before"
test "$(kubectl get deployment -n databases mariadb postgres redis -o jsonpath='{range .items[*]}{.metadata.uid}{"="}{.metadata.resourceVersion}{"\n"}{end}' | sort)" = "$production_before"
test "$(kubectl get statefulset -n monitoring alertmanager-choms-monitoring-alertmanager prometheus-choms-monitoring-prometheus -o jsonpath='{range .items[*]}{.metadata.uid}{"="}{.metadata.resourceVersion}{"\n"}{end}' | sort)" = "$monitoring_before"

printf 'recovery_test=validated\n'
printf 'namespace=%s\n' "$NAMESPACE"
printf 'package=%s\n' "$BACKUP_STAMP"
printf 'config_files=%s\n' "$config_files"
printf 'mariadb artifact_bytes=%s databases=%s tables=%s rto_ms=%s\n' "$(stat -c %s "$BACKUP_DIR/mariadb-nextcloud.sql.gz")" "$mariadb_databases" "$mariadb_tables" "$((mariadb_end-mariadb_start))"
printf 'postgres artifact_bytes=%s schemas=%s tables=%s rto_ms=%s\n' "$(stat -c %s "$BACKUP_DIR/postgres-choms_platform.dump")" "$postgres_schemas" "$postgres_tables" "$((postgres_end-postgres_start))"
printf 'redis artifact_bytes=%s keys=%s rto_ms=%s\n' "$(stat -c %s "$BACKUP_DIR/redis-dump.rdb")" "$redis_keys" "$((redis_end-redis_start))"
printf 'temporary_endpoints=0\n'
printf 'unexpected_unhealthy_delta=0\n'
printf 'critical_alert_delta=0\n'
