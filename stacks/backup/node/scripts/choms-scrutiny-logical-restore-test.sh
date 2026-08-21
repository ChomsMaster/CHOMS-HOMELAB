#!/usr/bin/env bash

set -euo pipefail
set +x
umask 077

NAMESPACE=monitoring
NODE=choms-node-01
INFLUX_IMAGE='docker.io/library/influxdb@sha256:0bf6457dc1282f653d9e82186fad7e35138892364c7f81e5e2c47b551c65a49a'
PYTHON_IMAGE='docker.io/library/python@sha256:9ba6d8cbebf0fb6546ae71f2a1c14f6ffd2fdab83af7fa5669734ef30ad48844'
SCRUTINY_IMAGE='ghcr.io/analogj/scrutiny@sha256:18689773150d6b8b53c94a435f40f7b6e946fd4a6d40b44c64fa2154a5b38941'
BACKUP_HOST_ROOT=/mnt/choms-backups/scrutiny/logical/daily
POD="scrutiny-logical-restore-$(date -u +%Y%m%d%H%M%S)"

fail() {
  echo "ERROR: $1" >&2
  exit 1
}

cleanup() {
  kubectl delete pod "$POD" -n "$NAMESPACE" \
    --ignore-not-found=true --wait=true >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

test "$(kubectl config current-context)" = default ||
  fail "El contexto Kubernetes activo no es default"

manifest="$(cat <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: $POD
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: scrutiny-logical-restore-test
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
    image: $PYTHON_IMAGE
    imagePullPolicy: IfNotPresent
    command: [/bin/sh, -euc]
    args:
    - |
      source="\$(readlink -f /backup/latest)"
      case "\$source" in /backup/*) ;; *) exit 1 ;; esac
      test -s "\$source/SHA256SUMS"
      (cd "\$source" && sha256sum -c SHA256SUMS >/dev/null)
      mkdir -m 0700 /restore/config /restore/influxdb /restore/source-influx
      cp "\$source/scrutiny.db" /restore/config/scrutiny.db
      cp -a "\$source/influxdb/." /restore/source-influx/
      python3 - <<'PY'
      import sqlite3

      database = sqlite3.connect(
          "file:/restore/config/scrutiny.db?mode=ro", uri=True
      )
      result = database.execute("PRAGMA integrity_check").fetchone()
      tables = database.execute(
          "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
      ).fetchone()[0]
      database.close()
      if result != ("ok",) or tables < 1:
          raise SystemExit("SQLite restore validation failed")
      PY
      echo restore_copy=validated
      echo sqlite_integrity=validated
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: [ALL]
      readOnlyRootFilesystem: true
    resources:
      requests:
        cpu: 25m
        memory: 64Mi
      limits:
        cpu: 250m
        memory: 256Mi
    volumeMounts:
    - name: backup
      mountPath: /backup
      readOnly: true
    - name: restore
      mountPath: /restore
    - name: tmp
      mountPath: /tmp
  - name: influx-restore
    image: $INFLUX_IMAGE
    imagePullPolicy: IfNotPresent
    command: [/bin/sh, -euc]
    args:
    - |
      set +x
      umask 077
      export INFLUX_CONFIGS_PATH=/tmp/influx-configs
      stage=initialize
      initial_token="\$(head -c 48 /dev/urandom | base64 | tr -d '\n')"
      initial_password="\$(head -c 36 /dev/urandom | base64 | tr -d '\n')"
      finish() {
        status=\$?
        trap - EXIT INT TERM
        kill "\${influx_pid:-}" 2>/dev/null || true
        wait "\${influx_pid:-}" 2>/dev/null || true
        initial_token=
        initial_password=
        if [ "\$status" -ne 0 ]; then
          echo "restore_stage_failed=\$stage" >&2
        fi
        exit "\$status"
      }
      trap finish EXIT INT TERM
      stage=start_influxdb
      influxd \
        --bolt-path /restore/influxdb/influxd.bolt \
        --engine-path /restore/influxdb/engine \
        --sqlite-path /restore/influxdb/influxd.sqlite \
        --http-bind-address 127.0.0.1:8086 \
        >/tmp/influxd.log 2>&1 &
      influx_pid=\$!
      for attempt in \$(seq 1 60); do
        influx ping --host http://127.0.0.1:8086 >/dev/null 2>&1 && break
        [ "\$attempt" -lt 60 ] || exit 1
        sleep 1
      done
      stage=setup
      INFLUX_HOST=http://127.0.0.1:8086 \
      INFLUX_TOKEN="\$initial_token" \
        influx setup --force \
          --username restore-validation \
          --password "\$initial_password" \
          --org restore-validation \
          --bucket restore-validation >/tmp/setup.log 2>&1
      stage=full_restore
      INFLUX_HOST=http://127.0.0.1:8086 \
      INFLUX_TOKEN="\$initial_token" \
        timeout 12m influx restore --full /restore/source-influx \
          >/tmp/restore.log 2>&1
      stage=health
      INFLUX_HOST=http://127.0.0.1:8086 \
        influx ping >/dev/null 2>&1
      kill "\$influx_pid"
      wait "\$influx_pid" 2>/dev/null || true
      influx_pid=
      stage=verify_tsm
      influxd inspect verify-tsm \
        --engine-path /restore/influxdb/engine >/tmp/verify-tsm.log 2>&1
      stage=verify_wal
      if [ -d /restore/influxdb/engine/wal ] &&
         [ -n "\$(find /restore/influxdb/engine/wal -type f -print -quit)" ]; then
        influxd inspect verify-wal \
          --wal-path /restore/influxdb/engine/wal >/tmp/verify-wal.log 2>&1
      fi
      stage=verify_series
      influxd inspect verify-seriesfile \
        --data-path /restore/influxdb/engine/data >/tmp/verify-series.log 2>&1
      stage=complete
      trap - EXIT INT TERM
      rm -f /tmp/influxd.log /tmp/setup.log /tmp/restore.log \
        /tmp/verify-tsm.log /tmp/verify-wal.log /tmp/verify-series.log
      echo influx_restore=validated
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: [ALL]
      readOnlyRootFilesystem: true
    resources:
      requests:
        cpu: 100m
        memory: 256Mi
      limits:
        cpu: 1000m
        memory: 1Gi
    volumeMounts:
    - name: restore
      mountPath: /restore
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
      limits:
        cpu: 1000m
        memory: 2Gi
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
      sizeLimit: 128Mi
EOF
)"

printf '%s\n' "$manifest" | kubectl apply --dry-run=server -f - >/dev/null
set +e
printf '%s\n' "$manifest" | kubectl diff -f - >/dev/null
diff_status=$?
set -e
[ "$diff_status" -eq 0 ] || [ "$diff_status" -eq 1 ] ||
  fail "kubectl diff falló con código $diff_status"
printf '%s\n' "$manifest" | kubectl apply -f - >/dev/null
unset manifest

for _ in $(seq 1 120); do
  phase="$(kubectl get pod "$POD" -n "$NAMESPACE" -o jsonpath='{.status.phase}')"
  if [ "$phase" = Running ] && [ "$(
    kubectl get pod "$POD" -n "$NAMESPACE" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'
  )" = True ]; then
    break
  fi
  if [ "$phase" = Failed ]; then
    kubectl logs "$POD" -n "$NAMESPACE" -c influx-restore 2>/dev/null |
      grep '^restore_stage_failed=' >&2 || true
    fail "La restauración lógica aislada falló"
  fi
  sleep 5
done
test "$(
  kubectl get pod "$POD" -n "$NAMESPACE" \
    -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'
)" = True || fail "La restauración lógica aislada no arrancó"

for attempt in $(seq 1 90); do
  if kubectl exec "$POD" -n "$NAMESPACE" -c scrutiny -- sh -euc '
    test "$(curl -sS -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:8086/health)" = 200
    test "$(curl -sS -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:8080/api/health)" = 200
  ' >/dev/null 2>&1; then
    break
  fi
  [ "$attempt" -lt 90 ] ||
    fail "Los servicios restaurados no quedaron saludables"
  sleep 2
done

for init in restore-copy influx-restore; do
  test "$(
    kubectl get pod "$POD" -n "$NAMESPACE" \
      -o jsonpath="{.status.initContainerStatuses[?(@.name=='$init')].state.terminated.exitCode}"
  )" = 0 || fail "Falló el init container $init"
done

echo isolated_logical_restore=validated
echo sqlite_integrity=validated
echo influxdb_2_2_restore=validated
echo scrutiny_0_8_2_health=validated

cleanup
trap - EXIT INT TERM
