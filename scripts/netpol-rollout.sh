#!/usr/bin/env bash
# Opt-in operator tool. Never invoked by validate.sh or CI.
set -euo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ $# -ne 3 || $1 != --execute ]]; then
  echo "Usage: $0 --execute EXPLICIT_CONTEXT ONE_NAMESPACE"
  echo "Read docs/operations/NETWORK_POLICIES.md and complete prerequisites first."
  exit 2
fi
context_name="$2"
namespace_name="$3"
case "$namespace_name" in
  apps|cert-manager|colegio-maria-rosario-staging|databases|diagnostics|filebrowser|logging|media|metallb-system|monitoring|nfs-provisioner|security|traefik) ;;
  *) echo 'Namespace outside the reviewed inventory.' >&2; exit 2 ;;
esac
policy_file="$repo_root/stacks/kubernetes/networkpolicies/$namespace_name/policies.yaml"
kubectl_args=(--context "$context_name" --namespace "$namespace_name")
echo "Target: context=$context_name namespace=$namespace_name"
# First-install tool: refuse to overwrite or implicitly replace existing policy.
existing="$(kubectl "${kubectl_args[@]}" get networkpolicy -o name)"
if [[ -n $existing ]]; then
  echo 'Existing policies detected. Stop and prepare a separate reviewed migration.' >&2
  exit 1
fi
kubectl "${kubectl_args[@]}" get deployment,statefulset,daemonset,pods
kubectl "${kubectl_args[@]}" apply --dry-run=server -f "$policy_file" >/dev/null
work_dir="$(mktemp -d)"
trap 'rm -rf -- "$work_dir"' EXIT
python3 - "$policy_file" "$work_dir" <<'PY'
from pathlib import Path
import sys
import yaml
docs = list(yaml.safe_load_all(Path(sys.argv[1]).read_text()))
for name, subset in [('exceptions', [d for d in docs if d['metadata']['name'] != 'choms-default-deny']),
                     ('deny', [d for d in docs if d['metadata']['name'] == 'choms-default-deny'])]:
    Path(sys.argv[2], name + '.yaml').write_text(yaml.safe_dump_all(subset))
PY
echo "Rollback (only policies introduced by this reviewed file):"
printf 'kubectl --context %q --namespace %q delete -f %q\n' "$context_name" "$namespace_name" "$policy_file"
# Exceptions already isolate selected directions, so even this phase needs checks.
# No automatic rollback: operators retain evidence and decide with the runbook.
kubectl "${kubectl_args[@]}" apply -f "$work_dir/exceptions.yaml"
kubectl "${kubectl_args[@]}" apply -f "$work_dir/deny.yaml"
kubectl "${kubectl_args[@]}" get networkpolicy,deployment,statefulset,daemonset,pods
echo 'STOP: complete the functional checks in the runbook before another namespace.'
