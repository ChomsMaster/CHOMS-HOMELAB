#!/usr/bin/env bash

set -euo pipefail
umask 077

NAMESPACE=monitoring
DEPLOYMENT=scrutiny
NODE=choms-node-01
IMAGE='ghcr.io/analogj/scrutiny@sha256:18689773150d6b8b53c94a435f40f7b6e946fd4a6d40b44c64fa2154a5b38941'
BACKUP_HOST_ROOT=/mnt/choms-backups/scrutiny/bootstrap
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PREFLIGHT_POD="scrutiny-backup-preflight-${STAMP,,}"
BACKUP_JOB="scrutiny-cold-backup-${STAMP,,}"
ORIGINAL_REPLICAS=""
INTERRUPTION_STARTED=0
RESTORE_ATTEMPTED=0

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

cleanup_resources() {
  kubectl delete pod "$PREFLIGHT_POD" -n "$NAMESPACE" \
    --ignore-not-found=true --wait=true >/dev/null 2>&1 || true
  kubectl delete job "$BACKUP_JOB" -n "$NAMESPACE" \
    --ignore-not-found=true --wait=true >/dev/null 2>&1 || true
}

restore_production() {
  if [ "$INTERRUPTION_STARTED" -eq 1 ] && [ "$RESTORE_ATTEMPTED" -eq 0 ]; then
    RESTORE_ATTEMPTED=1
    kubectl scale deployment "$DEPLOYMENT" -n "$NAMESPACE" \
      --replicas="$ORIGINAL_REPLICAS" >/dev/null || true
    kubectl rollout status deployment/"$DEPLOYMENT" -n "$NAMESPACE" \
      --timeout=180s >/dev/null || true
  fi
}

cleanup() {
  status=$?
  restore_production
  cleanup_resources
  exit "$status"
}

trap cleanup EXIT INT TERM

test "$(kubectl config current-context)" = default ||
  fail "El contexto Kubernetes activo no es default"

ORIGINAL_REPLICAS="$(
  kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" \
    -o jsonpath='{.spec.replicas}'
)"
test "$ORIGINAL_REPLICAS" = 1 ||
  fail "Scrutiny no parte de una réplica"

test "$(
  kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" \
    -o jsonpath='{.status.readyReplicas}'
)" = 1 || fail "Scrutiny no parte Ready 1/1"

cat <<EOF | apply_temporary
apiVersion: v1
kind: Pod
metadata:
  name: $PREFLIGHT_POD
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: scrutiny-backup-preflight
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
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: preflight
    image: $IMAGE
    imagePullPolicy: IfNotPresent
    command: [/bin/sh, -euc]
    args:
    - |
      test -r /source-config/scrutiny.db
      test -r /source-influxdb/influxd.bolt
      test -d /source-influxdb/engine
      mkdir -p /backup/scrutiny/bootstrap
      chmod 0700 /backup/scrutiny /backup/scrutiny/bootstrap
      probe=/backup/scrutiny/bootstrap/.preflight-\$\$
      mkdir -m 0700 "\$probe"
      test "\$(stat -c %a "\$probe")" = 700
      rmdir "\$probe"
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: [ALL]
      readOnlyRootFilesystem: true
    resources:
      requests:
        cpu: 10m
        memory: 16Mi
      limits:
        cpu: 100m
        memory: 64Mi
    volumeMounts:
    - name: source-config
      mountPath: /source-config
      readOnly: true
    - name: source-influxdb
      mountPath: /source-influxdb
      readOnly: true
    - name: backup
      mountPath: /backup
  volumes:
  - name: source-config
    hostPath:
      path: /data/docker/scrutiny/config
      type: Directory
  - name: source-influxdb
    hostPath:
      path: /data/docker/scrutiny/influxdb
      type: Directory
  - name: backup
    hostPath:
      path: /mnt/choms-backups
      type: Directory
EOF

kubectl wait pod/"$PREFLIGHT_POD" -n "$NAMESPACE" \
  --for=jsonpath='{.status.phase}'=Succeeded --timeout=120s >/dev/null ||
  fail "El preflight de montajes no terminó correctamente"
kubectl delete pod "$PREFLIGHT_POD" -n "$NAMESPACE" \
  --wait=true >/dev/null

echo "Iniciando interrupción controlada de Scrutiny."
INTERRUPTION_STARTED=1
INTERRUPTION_EPOCH="$(date +%s)"

kubectl scale deployment "$DEPLOYMENT" -n "$NAMESPACE" --replicas=0 >/dev/null

for _ in $(seq 1 60); do
  count="$(kubectl get pods -n "$NAMESPACE" -l app=scrutiny --no-headers 2>/dev/null | wc -l)"
  [ "$count" -eq 0 ] && break
  sleep 1
done

test "$(kubectl get pods -n "$NAMESPACE" -l app=scrutiny --no-headers 2>/dev/null | wc -l)" -eq 0 ||
  fail "Scrutiny no terminó dentro del timeout"

cat <<EOF | apply_temporary
apiVersion: batch/v1
kind: Job
metadata:
  name: $BACKUP_JOB
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: scrutiny-cold-backup
spec:
  backoffLimit: 0
  activeDeadlineSeconds: 300
  ttlSecondsAfterFinished: 600
  template:
    metadata:
      labels:
        app.kubernetes.io/name: scrutiny-cold-backup
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
        runAsGroup: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: backup
        image: $IMAGE
        imagePullPolicy: IfNotPresent
        command: [/bin/sh, -euc]
        args:
        - |
          umask 077
          root=/backup/scrutiny/bootstrap
          partial="\$root/.partial-$STAMP"
          final="\$root/$STAMP"
          lock=/backup/scrutiny/.bootstrap.lock
          cleanup() { rmdir "\$lock" 2>/dev/null || true; }
          trap cleanup EXIT INT TERM
          mkdir -p "\$root"
          chmod 0700 /backup/scrutiny "\$root"
          mkdir "\$lock" || { echo 'ERROR: otro backup está activo' >&2; exit 1; }
          test ! -e "\$partial"
          test ! -e "\$final"
          mkdir -m 0700 "\$partial"
          mkdir -m 0700 "\$partial/config" "\$partial/influxdb"
          tar -C /source-config -cf - . | \
            tar --no-same-owner --no-same-permissions -C "\$partial/config" -xf -
          tar -C /source-influxdb -cf - . | \
            tar --no-same-owner --no-same-permissions -C "\$partial/influxdb" -xf -
          find "\$partial/config" "\$partial/influxdb" -xdev -type f \
            -printf '%P\t%s\n' | LC_ALL=C sort > "\$partial/FILES.txt"
          test -s "\$partial/FILES.txt"
          (
            cd "\$partial"
            find config influxdb -xdev -type f -print0 | LC_ALL=C sort -z | \
              xargs -0 sha256sum > SHA256SUMS
            sha256sum -c SHA256SUMS >/dev/null
          )
          cat > "\$partial/metadata.txt" <<META
          Created: $STAMP
          Scrutiny image: $IMAGE
          InfluxDB version: 2.2.0
          Backup mode: cold
          Source mounted read-only: yes
          META
          chmod -R go-rwx "\$partial"
          mv "\$partial" "\$final"
          ln -sfn "$STAMP" "\$root/latest"
          echo 'backup_publication=validated'
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop: [ALL]
          readOnlyRootFilesystem: true
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
            ephemeral-storage: 16Mi
          limits:
            cpu: 500m
            memory: 256Mi
            ephemeral-storage: 64Mi
        volumeMounts:
        - name: source-config
          mountPath: /source-config
          readOnly: true
        - name: source-influxdb
          mountPath: /source-influxdb
          readOnly: true
        - name: backup
          mountPath: /backup
      volumes:
      - name: source-config
        hostPath:
          path: /data/docker/scrutiny/config
          type: Directory
      - name: source-influxdb
        hostPath:
          path: /data/docker/scrutiny/influxdb
          type: Directory
      - name: backup
        hostPath:
          path: /mnt/choms-backups
          type: Directory
EOF

kubectl wait job/"$BACKUP_JOB" -n "$NAMESPACE" \
  --for=condition=Complete --timeout=330s >/dev/null ||
  fail "El Job de backup no terminó correctamente"

kubectl logs job/"$BACKUP_JOB" -n "$NAMESPACE" | grep -qx 'backup_publication=validated' ||
  fail "El Job no confirmó publicación validada"

restore_production

elapsed="$(($(date +%s) - INTERRUPTION_EPOCH))"
test "$elapsed" -lt 600 || fail "La interrupción superó diez minutos"

test "$(
  kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" \
    -o jsonpath='{.status.readyReplicas}'
)" = 1 || fail "Scrutiny no volvió a 1/1"

kubectl delete job "$BACKUP_JOB" -n "$NAMESPACE" --wait=true >/dev/null

trap - EXIT INT TERM
cleanup_resources

echo "backup_release=$STAMP"
echo "interruption_seconds=$elapsed"
echo "production_replicas=1"
