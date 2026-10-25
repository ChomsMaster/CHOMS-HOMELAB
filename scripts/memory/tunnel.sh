#!/usr/bin/env bash
# Foreground helper for future internal Services; refuses absent/invalid endpoints.
set -euo pipefail
# Self-contained so the helper can be used without sourcing another checkout file.
fail() { printf 'ERROR: %s\n' "$1" >&2; exit 1; }
valid_ssh_target() { [[ $1 =~ ^([a-zA-Z_][a-zA-Z0-9_.-]*@)?[a-zA-Z0-9][a-zA-Z0-9.-]*$ ]]; }
valid_local_port() { [[ $1 =~ ^[1-9][0-9]{0,4}$ ]] && (( 10#$1 <= 65535 )); }
valid_cluster_ip() {
  local octet
  local -a octets
  [[ $1 =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] || return 1
  IFS=. read -r -a octets <<< "$1"
  for octet in "${octets[@]}"; do
    [[ $octet == 0 || $octet != 0* ]] || return 1
    (( 10#$octet <= 255 )) || return 1
  done
  (( 10#${octets[0]} > 0 && 10#${octets[0]} < 224 && 10#${octets[0]} != 127 )) || return 1
  [[ ${octets[0]}.${octets[1]} != 169.254 ]]
}

(( $# >= 2 && $# <= 3 )) || fail 'Usage: memory/tunnel.sh cognee-api|cognee-mcp|canvas user@host [local-port]'
component=$1
target=$2
case "$component" in
  cognee-api) namespace=choms-memory; service=cognee-api; default_port=18000 ;;
  cognee-mcp) namespace=choms-memory; service=cognee-mcp; default_port=18001 ;;
  canvas) namespace=openhands; service=agent-canvas; default_port=18002 ;;
  *) fail 'Unknown internal component' ;;
esac
local_port=${3:-$default_port}
valid_ssh_target "$target" || fail 'Invalid SSH destination'
valid_local_port "$local_port" || fail 'Invalid local port'
ssh_options=(-F /dev/null -T -o BatchMode=yes -o StrictHostKeyChecking=yes
  -o ConnectTimeout=6 -o ConnectionAttempts=1 -o UpdateHostKeys=no
  -o ForwardAgent=no -o IdentityAgent=none -o ExitOnForwardFailure=yes
  -o ServerAliveInterval=30 -o ServerAliveCountMax=3)
# All interpolated remote arguments come from the closed case statement above.
# shellcheck disable=SC2029 # Both expanded values are constants from the closed case above.
endpoint=$(ssh "${ssh_options[@]}" "$target" \
  "kubectl --request-timeout=15s --namespace=$namespace get service $service -o 'jsonpath={.spec.clusterIP}{\" \"}{.spec.ports[0].port}'") \
  || fail 'Internal Service discovery failed; component may not be deployed'
read -r cluster_ip remote_port extra <<< "$endpoint"
[[ -z ${extra:-} && $endpoint != *$'\n'* ]] || fail 'Ambiguous Service response'
valid_cluster_ip "$cluster_ip" || fail 'Invalid IPv4 ClusterIP'
valid_local_port "$remote_port" || fail 'Invalid Service port'
exec ssh "${ssh_options[@]}" -N -L "127.0.0.1:${local_port}:${cluster_ip}:${remote_port}" "$target"
