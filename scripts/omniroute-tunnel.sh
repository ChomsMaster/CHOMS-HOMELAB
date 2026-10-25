#!/usr/bin/env bash
# Foreground, loopback-only access to the private OmniRoute API.
set -euo pipefail

fail() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 1
}

valid_ssh_target() {
  [[ $1 =~ ^([a-zA-Z_][a-zA-Z0-9_.-]*@)?[a-zA-Z0-9][a-zA-Z0-9.-]*$ ]]
}

valid_local_port() {
  [[ $1 =~ ^[1-9][0-9]{0,4}$ ]] && (( 10#$1 <= 65535 ))
}

valid_cluster_ip() {
  local value=$1 octet
  local -a octets
  [[ $value =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] || return 1
  IFS=. read -r -a octets <<< "$value"
  for octet in "${octets[@]}"; do
    [[ $octet == 0 || $octet != 0* ]] || return 1
    (( 10#$octet <= 255 )) || return 1
  done
  (( 10#${octets[0]} > 0 && 10#${octets[0]} < 224 && 10#${octets[0]} != 127 )) || return 1
  [[ ${octets[0]}.${octets[1]} != 169.254 ]]
}

main() {
  (( $# <= 2 )) || fail 'Usage: omniroute-tunnel.sh [user@host] [local-port]'
  local target=${1:-${OMNIROUTE_SSH_TARGET:-}}
  local local_port=${2:-${OMNIROUTE_LOCAL_PORT:-20129}}
  local cluster_ip
  local -a ssh_options=(
    -F /dev/null -T
    -o BatchMode=yes -o ConnectTimeout=6 -o ConnectionAttempts=1
    -o StrictHostKeyChecking=yes -o UpdateHostKeys=no
    -o ForwardAgent=no -o IdentityAgent=none
    -o ExitOnForwardFailure=yes
    -o ServerAliveInterval=30 -o ServerAliveCountMax=3
  )
  valid_ssh_target "$target" || fail 'A valid SSH destination argument or OMNIROUTE_SSH_TARGET is required'
  valid_local_port "$local_port" || fail 'Invalid local port'
  command -v ssh >/dev/null 2>&1 || fail 'ssh is required'
  cluster_ip=$(ssh "${ssh_options[@]}" "$target" \
    "kubectl --request-timeout=15s --namespace=omniroute get service omniroute -o 'jsonpath={.spec.clusterIP}'") \
    || fail 'Service discovery failed'
  valid_cluster_ip "$cluster_ip" || fail 'Service discovery returned an invalid IPv4 ClusterIP'
  exec ssh "${ssh_options[@]}" -N \
    -L "127.0.0.1:${local_port}:${cluster_ip}:20129" "$target"
}

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
  main "$@"
fi
