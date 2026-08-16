#!/bin/bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: choms-kubernetes-workload-audit.sh [--context NAME] [--kubeconfig PATH]

Read-only Kubernetes workload inventory. The script never reads Secret objects.
USAGE
}

context=""
kubeconfig=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --context)
      [[ $# -ge 2 ]] || { echo "ERROR: --context requires a value" >&2; exit 2; }
      context="$2"
      shift 2
      ;;
    --kubeconfig)
      [[ $# -ge 2 ]] || { echo "ERROR: --kubeconfig requires a value" >&2; exit 2; }
      kubeconfig="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

for command in kubectl jq sort awk find sed xargs date mktemp rm; do
  command -v "$command" >/dev/null 2>&1 || {
    echo "ERROR: required command not found: $command" >&2
    exit 1
  }
done

kubectl_args=()
[[ -z "$context" ]] || kubectl_args+=(--context "$context")
[[ -z "$kubeconfig" ]] || kubectl_args+=(--kubeconfig "$kubeconfig")
k=(kubectl "${kubectl_args[@]}")

"${k[@]}" cluster-info >/dev/null 2>&1 || {
  echo "ERROR: Kubernetes cluster is not reachable with the selected credentials" >&2
  exit 1
}

workloads_json="$(mktemp)"
pods_json="$(mktemp)"
trap 'rm -f "$workloads_json" "$pods_json"' EXIT

"${k[@]}" get deployment,statefulset,daemonset,job,cronjob -A -o json >"$workloads_json"
"${k[@]}" get pods -A -o json >"$pods_json"

echo "CHOMS Platforms Kubernetes workload audit"
echo "Generated UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Context: $("${k[@]}" config current-context)"
echo

echo "== Nodes =="
"${k[@]}" get nodes \
  -o custom-columns=NAME:.metadata.name,READY:.status.conditions[-1].status,VERSION:.status.nodeInfo.kubeletVersion \
  --no-headers | sort
echo

echo "== Namespaces =="
"${k[@]}" get namespaces \
  -o custom-columns=NAME:.metadata.name,PHASE:.status.phase \
  --no-headers | sort
echo

echo "== Workloads (TSV) =="
echo -e "NAMESPACE\tKIND\tNAME\tOWNER\tREPLICAS\tSTRATEGY\tIMAGES\tREADINESS\tLIVENESS\tSTARTUP\tRESOURCES\tSERVICE_ACCOUNT\tPERSISTENT_VOLUMES\tSECURITY"
jq -r '
  .items[] |
  def ps: if .kind == "CronJob" then .spec.jobTemplate.spec.template.spec else .spec.template.spec end;
  def cs: ((ps.initContainers // []) + (ps.containers // []));
  def owner:
    if (.metadata.labels["app.kubernetes.io/managed-by"] // "") == "Helm"
       or (.metadata.annotations["meta.helm.sh/release-name"] // "") != ""
    then "Helm:" + (.metadata.annotations["meta.helm.sh/release-name"] // .metadata.labels["app.kubernetes.io/instance"] // "unknown")
    elif .metadata.namespace == "kube-system" then "K3s/system"
    else "direct/unknown" end;
  def replicas:
    if .kind == "DaemonSet" then (.status.desiredNumberScheduled // 0)
    elif .kind == "CronJob" then (.spec.suspend // false | not)
    else (.spec.replicas // 1) end;
  def strategy:
    if .kind == "Deployment" then (.spec.strategy.type // "RollingUpdate")
    elif .kind == "StatefulSet" or .kind == "DaemonSet" then (.spec.updateStrategy.type // "RollingUpdate")
    else "n/a" end;
  def probe($name): [cs[] | select(.[$name] != null) | .name] | if length == 0 then "none" else join(",") end;
  def resources: [cs[] | .name + "[req=" + ((.resources.requests // {}) | to_entries | map(.key+"="+(.value|tostring)) | join(",")) + ";lim=" + ((.resources.limits // {}) | to_entries | map(.key+"="+(.value|tostring)) | join(",")) + "]"] | join(";");
  def volumes: [(ps.volumes // [])[] | if .persistentVolumeClaim then "pvc:"+.persistentVolumeClaim.claimName elif .hostPath then "hostPath:"+.hostPath.path else empty end] | join(",");
  def security: "pod="+((ps.securityContext // {})|tostring)+";containers="+([cs[] | .name+"="+((.securityContext // {})|tostring)]|join(";"))+";hostNetwork="+((ps.hostNetwork//false)|tostring)+";hostPID="+((ps.hostPID//false)|tostring);
  [.metadata.namespace,.kind,.metadata.name,owner,(replicas|tostring),strategy,([cs[]|.name+"="+.image]|join(";")),probe("readinessProbe"),probe("livenessProbe"),probe("startupProbe"),resources,(ps.serviceAccountName//"default"),volumes,security] | @tsv
' "$workloads_json" | sort
echo

echo "== Effective container images (TSV) =="
echo -e "NAMESPACE\tPOD\tCONTAINER\tREPORTED_IMAGE\tIMAGE_ID\tREADY\tRESTARTS"
jq -r '.items[] | select(.status.phase=="Running") | .metadata.namespace as $ns | .metadata.name as $pod | ((.status.initContainerStatuses//[])+(.status.containerStatuses//[]))[] | [$ns,$pod,.name,.image,.imageID,(.ready|tostring),(.restartCount|tostring)] | @tsv' "$pods_json" | sort
echo

echo "== Findings: mutable or latest images =="
jq -r '
  .items[] |
  .metadata.namespace as $ns | .kind as $kind | .metadata.name as $name |
  (if .kind=="CronJob" then .spec.jobTemplate.spec.template.spec else .spec.template.spec end) as $ps |
  (($ps.initContainers//[])+($ps.containers//[]))[] |
  select(.image | contains("@sha256:") | not) |
  [$ns,$kind,$name,.name,.image,(if (.image|endswith(":latest")) then "latest" else "tag" end)] | @tsv
' "$workloads_json" | sort
echo

echo "== Findings: missing probes =="
jq -r '
  .items[] |
  .metadata.namespace as $ns | .kind as $kind | .metadata.name as $name |
  (if .kind=="CronJob" then .spec.jobTemplate.spec.template.spec else .spec.template.spec end) as $ps |
  ($ps.containers//[])[] |
  select(.readinessProbe==null or .livenessProbe==null or .startupProbe==null) |
  [$ns,$kind,$name,.name,(if .readinessProbe then "yes" else "no" end),(if .livenessProbe then "yes" else "no" end),(if .startupProbe then "yes" else "no" end)] | @tsv
' "$workloads_json" | sort
echo

echo "== Findings: missing requests or limits =="
jq -r '
  .items[] |
  .metadata.namespace as $ns | .kind as $kind | .metadata.name as $name |
  (if .kind=="CronJob" then .spec.jobTemplate.spec.template.spec else .spec.template.spec end) as $ps |
  (($ps.initContainers//[])+($ps.containers//[]))[] |
  select((.resources.requests//{}|length)==0 or (.resources.limits//{}|length)==0) |
  [$ns,$kind,$name,.name,(if (.resources.requests//{}|length)>0 then "yes" else "no" end),(if (.resources.limits//{}|length)>0 then "yes" else "no" end)] | @tsv
' "$workloads_json" | sort
echo

echo "== Findings: sensitive security settings =="
jq -r '
  .items[] |
  .metadata.namespace as $ns | .kind as $kind | .metadata.name as $name |
  (if .kind=="CronJob" then .spec.jobTemplate.spec.template.spec else .spec.template.spec end) as $ps |
  ([($ps.volumes//[])[] | select(.hostPath) | .hostPath.path] | join(",")) as $hostpaths |
  (($ps.initContainers//[])+($ps.containers//[]))[] |
  select((.securityContext.privileged//false) or ($ps.hostNetwork//false) or ($ps.hostPID//false) or ($hostpaths!="") or ((.securityContext.capabilities.add//[])|length)>0) |
  [$ns,$kind,$name,.name,(.securityContext.privileged//false),($ps.hostNetwork//false),($ps.hostPID//false),$hostpaths,((.securityContext.capabilities.add//[])|join(","))] | @tsv
' "$workloads_json" | sort
echo

echo "== PVCs =="
"${k[@]}" get pvc -A \
  -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,CLASS:.spec.storageClassName,CAPACITY:.status.capacity.storage \
  --no-headers | sort
echo

echo "== Helm releases =="
if command -v helm >/dev/null 2>&1; then
  helm_args=()
  [[ -z "$kubeconfig" ]] || helm_args+=(--kubeconfig "$kubeconfig")
  [[ -z "$context" ]] || helm_args+=(--kube-context "$context")
  helm "${helm_args[@]}" list -A -o json |
    jq -r '.[] | [.namespace,.name,.chart,.app_version,.status] | @tsv' | sort
else
  echo "INFO: helm not installed; release inventory skipped"
fi
echo

repo_root="${CHOMS_REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
echo "== Git image declarations =="
if [[ -d "$repo_root/stacks/kubernetes" ]]; then
  find "$repo_root/stacks/kubernetes" -type f \( -name '*.yaml' -o -name '*.yml' \) -print0 |
    sort -z |
    xargs -0 awk '/^[[:space:]]*image:[[:space:]]*/ {value=$0; sub(/^[[:space:]]*image:[[:space:]]*/,"",value); print FILENAME ":" FNR "\t" value}' |
    sed "s#$repo_root/##" |
    sort
else
  echo "INFO: Git manifest directory unavailable; runtime audit is complete but Git image scan was skipped"
fi
