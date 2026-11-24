#!/usr/bin/env bash
set -euo pipefail

here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
namespace=choms-project-manager
mode=${1:-}
image=${2:-}
case "$mode" in
  namespace-plan|namespace-apply|plan|apply|edge-plan|edge-apply) ;;
  *) echo "Uso: $0 {namespace-plan|namespace-apply|plan|apply|edge-plan|edge-apply} [imagen@sha256:digest]" >&2; exit 2 ;;
esac

manifest=$(mktemp)
trap 'rm -f -- "$manifest"' EXIT
case "$mode" in
  namespace-*) cp "$here/namespace.yaml" "$manifest" ;;
  edge-*) cp "$here/edge.yaml" "$manifest" ;;
  *)
    if [[ ! "$image" =~ ^[a-z0-9./:_-]+@sha256:[a-f0-9]{64}$ ]]; then
      echo 'La referencia de imagen debe incluir un digest SHA-256.' >&2
      exit 2
    fi
    for secret in career-app career-db-admin career-seed; do
      kubectl -n "$namespace" get secret "$secret" -o name >/dev/null
    done
    sed "s|CAREER_IMAGE_REF|$image|g" "$here/workload.yaml" > "$manifest"
    ;;
esac

kubectl apply --dry-run=client --validate=strict -f "$manifest" -o name
kubectl apply --dry-run=server --validate=strict -f "$manifest" -o name
set +e
kubectl diff -f "$manifest"
status=$?
set -e
if (( status > 1 )); then
  exit "$status"
fi

case "$mode" in
  namespace-apply|apply|edge-apply)
    kubectl apply -f "$manifest"
    if [[ "$mode" == apply ]]; then
      kubectl -n "$namespace" rollout status statefulset/project-db --timeout=180s
      kubectl -n "$namespace" rollout status deployment/choms-project-manager --timeout=180s
      kubectl -n "$namespace" get pods,pvc,endpointslice
      kubectl diff -f "$manifest"
    fi
    ;;
esac
