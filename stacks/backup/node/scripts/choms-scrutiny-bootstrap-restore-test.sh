#!/usr/bin/env bash

set -euo pipefail
umask 077

NAMESPACE=monitoring
NODE=choms-node-01
SCRUTINY_IMAGE='ghcr.io/analogj/scrutiny@sha256:18689773150d6b8b53c94a435f40f7b6e946fd4a6d40b44c64fa2154a5b38941'
PYTHON_IMAGE='docker.io/library/python@sha256:9ba6d8cbebf0fb6546ae71f2a1c14f6ffd2fdab83af7fa5669734ef30ad48844'
BACKUP_HOST_ROOT=/mnt/choms-backups/scrutiny/bootstrap
POD="scrutiny-bootstrap-restore-$(date -u +%Y%m%d%H%M%S)"

cleanup() {
  kubectl delete pod "$POD" -n "$NAMESPACE" \
    --ignore-not-found=true --wait=true >/dev/null 2>&1 || true
}

fail() {
  echo "ERROR: $1" >&2
  exit 1
}

apply_temporary() {
  manifest="$(cat)"
  printf '%s\n' "$manifest" | kubectl apply --dry-run=server -f - >/dev/null
  set +e
  printf '%s\n' "$manifest" | kubectl diff -f - >/dev/null
  diff_status=$?
  set -e
  [ "$diff_status" -eq 0 ] || [ "$diff_status" -eq 1 ] ||
    fail "kubectl diff falló con código $diff_status"
  printf '%s\n' "$manifest" | kubectl apply -f - >/dev/null
  unset manifest
}

trap cleanup EXIT INT TERM

test "$(kubectl config current-context)" = default ||
  fail "El contexto Kubernetes activo no es default"

cat <<EOF | apply_temporary
apiVersion: v1
kind: Pod
metadata:
  name: $POD
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: scrutiny-bootstrap-restore-test
spec:
  automountServiceAccountToken: false
  restartPolicy: Never
  nodeSelector:
    kubernetes.io/hostname: $NODE
  tolerations:
  - key: node-role.kubernetes.io/control-plane
    operator: Exists
    effect: NoSchedule
  securityContext:
    runAsUser: 0
    runAsGroup: 0
    seccompProfile:
      type: RuntimeDefault
  initContainers:
  - name: restore-copy
    image: $SCRUTINY_IMAGE
    imagePullPolicy: IfNotPresent
    command: [/bin/sh, -euc]
    args:
    - |
      root=/backup
      source="\$(readlink -f "\$root/latest")"
      case "\$source" in "\$root"/*) ;; *) exit 1 ;; esac
      test -d "\$source/config"
      test -d "\$source/influxdb/engine"
      test -s "\$source/influxdb/influxd.bolt"
      (cd "\$source" && sha256sum -c SHA256SUMS >/dev/null)
      mkdir -m 0700 /restore/config /restore/influxdb
      tar -C "\$source/config" -cf - . | \
        tar --no-same-owner --no-same-permissions -C /restore/config -xf -
      tar -C "\$source/influxdb" -cf - . | \
        tar --no-same-owner --no-same-permissions -C /restore/influxdb -xf -
      echo 'restore_copy=validated'
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: [ALL]
      readOnlyRootFilesystem: true
    resources:
      requests:
        cpu: 50m
        memory: 64Mi
      limits:
        cpu: 500m
        memory: 256Mi
    volumeMounts:
    - name: backup
      mountPath: /backup
      readOnly: true
    - name: restore
      mountPath: /restore
  - name: sqlite-integrity
    image: $PYTHON_IMAGE
    imagePullPolicy: IfNotPresent
    command: [python3, -c]
    args:
    - |
      import sqlite3
      uri = "file:/restore/config/scrutiny.db?mode=ro"
      connection = sqlite3.connect(uri, uri=True)
      result = connection.execute("PRAGMA integrity_check").fetchone()
      table_count = connection.execute(
          "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
      ).fetchone()[0]
      connection.close()
      if result != ("ok",) or table_count < 1:
          raise SystemExit("SQLite integrity validation failed")
      print("sqlite_integrity=ok")
      print("sqlite_structure=present")
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: [ALL]
      readOnlyRootFilesystem: true
    resources:
      requests:
        cpu: 10m
        memory: 32Mi
      limits:
        cpu: 100m
        memory: 64Mi
    volumeMounts:
    - name: restore
      mountPath: /restore
      readOnly: true
  - name: influx-integrity
    image: $SCRUTINY_IMAGE
    imagePullPolicy: IfNotPresent
    command: [/bin/sh, -euc]
    args:
    - |
      check() {
        name="\$1"; shift
        if "\$@" >/tmp/"\$name".log 2>&1; then
          echo "\$name=ok"
        else
          echo "\$name=failed" >&2
          exit 1
        fi
      }
      check influx_tsm influxd inspect verify-tsm --engine-path /restore/influxdb/engine
      check influx_wal influxd inspect verify-wal --wal-path /restore/influxdb/engine/wal
      check influx_series influxd inspect verify-seriesfile --data-path /restore/influxdb/engine/data
      check influx_tombstone influxd inspect verify-tombstone --engine-path /restore/influxdb/engine
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: [ALL]
      readOnlyRootFilesystem: true
    resources:
      requests:
        cpu: 50m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 512Mi
    volumeMounts:
    - name: restore
      mountPath: /restore
      readOnly: true
    - name: tmp
      mountPath: /tmp
  containers:
  - name: scrutiny
    image: $SCRUTINY_IMAGE
    imagePullPolicy: IfNotPresent
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: [ALL]
    resources:
      requests:
        cpu: 100m
        memory: 256Mi
        ephemeral-storage: 32Mi
      limits:
        cpu: 1000m
        memory: 2Gi
        ephemeral-storage: 256Mi
    volumeMounts:
    - name: restore
      mountPath: /opt/scrutiny/config
      subPath: config
    - name: restore
      mountPath: /opt/scrutiny/influxdb
      subPath: influxdb
  volumes:
  - name: backup
    hostPath:
      path: $BACKUP_HOST_ROOT
      type: Directory
  - name: restore
    emptyDir:
      sizeLimit: 1Gi
  - name: tmp
    emptyDir:
      sizeLimit: 64Mi
EOF

kubectl wait pod/"$POD" -n "$NAMESPACE" \
  --for=condition=Ready --timeout=300s >/dev/null ||
  fail "La restauración aislada no arrancó"

for attempt in $(seq 1 90); do
  if kubectl exec "$POD" -n "$NAMESPACE" -c scrutiny -- sh -euc '
    test "$(curl -sS -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:8086/health)" = 200
    test "$(curl -sS -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:8080/api/health)" = 200
  ' >/dev/null 2>&1; then
    break
  fi

  [ "$attempt" -lt 90 ] || fail "Los servicios restaurados no quedaron saludables"
  sleep 2
done

for init in restore-copy sqlite-integrity influx-integrity; do
  test "$(
    kubectl get pod "$POD" -n "$NAMESPACE" \
      -o jsonpath="{.status.initContainerStatuses[?(@.name=='$init')].state.terminated.exitCode}"
  )" = 0 || fail "Falló el init container $init"
done

echo 'isolated_restore=validated'
echo 'sqlite_integrity=validated'
echo 'influxdb_2_2_health=validated'
echo 'scrutiny_0_8_2_health=validated'

cleanup
trap - EXIT INT TERM
