#!/usr/bin/env bash
set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(CDPATH= cd -- "$script_dir/../../.." && pwd)"

operation="${1:-plan}"
helm_timeout="${HELM_TIMEOUT:-15m}"

usage() {
  echo "Usage: $0 [plan|apply]"
  echo
  echo "  plan   Validate every locked release using server-side dry-run."
  echo "  apply  Install or upgrade every locked release."
}

case "$operation" in
  plan|apply)
    ;;
  -h|--help|help)
    usage
    exit 0
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac

for command_name in helm kubectl; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "ERROR: required command not found: $command_name" >&2
    exit 1
  fi
done

add_repositories() {
  echo "========== HELM REPOSITORIES =========="

  helm repo add jetstack \
    https://charts.jetstack.io \
    --force-update

  helm repo add grafana \
    https://grafana.github.io/helm-charts \
    --force-update

  helm repo add grafana-community \
    https://grafana-community.github.io/helm-charts \
    --force-update

  helm repo add prometheus-community \
    https://prometheus-community.github.io/helm-charts \
    --force-update

  helm repo add nfs-subdir-external-provisioner \
    https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner/ \
    --force-update

  helm repo add traefik \
    https://traefik.github.io/charts \
    --force-update

  helm repo update
}

process_release() {
  local release_name="$1"
  local namespace_name="$2"
  local chart_name="$3"
  local chart_version="$4"
  shift 4

  local -a value_args=()

  while [ "$#" -gt 0 ]; do
    value_args+=("--values" "$repo_root/$1")
    shift
  done

  echo
  echo "--------------------------------------------------"
  echo "$namespace_name/$release_name"
  echo "Chart: $chart_name"
  echo "Version: $chart_version"
  echo "Operation: $operation"
  echo "--------------------------------------------------"

  if [ "$operation" = "plan" ]; then
    helm upgrade \
      --install "$release_name" "$chart_name" \
      --namespace "$namespace_name" \
      --create-namespace \
      --version "$chart_version" \
      "${value_args[@]}" \
      --dry-run=server \
      --hide-secret \
      >/dev/null

    echo "VALID"
    return
  fi

  helm upgrade \
    --install "$release_name" "$chart_name" \
    --namespace "$namespace_name" \
    --create-namespace \
    --version "$chart_version" \
    "${value_args[@]}" \
    --atomic \
    --wait \
    --wait-for-jobs \
    --timeout "$helm_timeout"
}

add_repositories

process_release \
  choms-nfs \
  nfs-provisioner \
  nfs-subdir-external-provisioner/nfs-subdir-external-provisioner \
  4.0.18 \
  stacks/kubernetes/nfs-provisioner/values.yaml

process_release \
  cert-manager \
  cert-manager \
  jetstack/cert-manager \
  v1.21.1 \
  stacks/kubernetes/cert-manager/values.yaml

process_release \
  traefik-k8s \
  traefik \
  traefik/traefik \
  41.1.0 \
  stacks/kubernetes/traefik/values-crd.yaml \
  stacks/kubernetes/traefik/values-https.yaml \
  stacks/kubernetes/traefik/values-metallb.yaml

process_release \
  choms-monitoring \
  monitoring \
  prometheus-community/kube-prometheus-stack \
  88.0.1 \
  stacks/kubernetes/monitoring/values.yaml

process_release \
  choms-loki \
  logging \
  grafana-community/loki \
  18.7.1 \
  stacks/kubernetes/logging/loki/values.yaml

process_release \
  choms-alloy \
  logging \
  grafana/alloy \
  1.11.0 \
  stacks/kubernetes/logging/alloy/values.yaml

echo
echo "========== COMPLETE =========="
echo "Operation completed: $operation"
