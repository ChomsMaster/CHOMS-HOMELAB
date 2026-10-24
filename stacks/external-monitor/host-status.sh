#!/usr/bin/env bash
set -euo pipefail
set +x

output_dir="/home/chomsmaster/choms-external-monitor/host-status"
output_file="${output_dir}/host-status.json"
firefox_container="firefox-web"
mkdir -p "$output_dir"
chmod 0755 "$output_dir"

while :; do
  disk_free="$(df -P / | awk 'NR==2 {gsub(/%/, "", $5); print 100-$5}')"
  inode_free="$(df -Pi / | awk 'NR==2 {gsub(/%/, "", $5); print 100-$5}')"
  # The helper is deliberately isolated by ProtectSystem=strict. Query PID 1's
  # mount namespace so this reports the host root rather than the helper view.
  root_options="$(findmnt -N 1 -n -o OPTIONS /)"
  root_read_only=false
  case ",${root_options}," in *,ro,*) root_read_only=true ;; esac
  temperature="null"
  if [[ -r /sys/class/thermal/thermal_zone0/temp ]]; then
    temperature="$(awk '{printf "%.1f", $1/1000}' /sys/class/thermal/thermal_zone0/temp)"
  fi
  throttled="null"
  if command -v vcgencmd >/dev/null 2>&1; then
    throttled="\"$(vcgencmd get_throttled 2>/dev/null | sed 's/^throttled=//' || true)\""
  fi
  firefox_running=false
  if [[ "$(docker inspect --format '{{.State.Running}}' "$firefox_container" 2>/dev/null || true)" == "true" ]]; then
    firefox_running=true
  fi
  tmp="${output_file}.tmp"
  printf '{"timestamp":%s,"disk_free_percent":%s,"inode_free_percent":%s,"root_read_only":%s,"temperature_c":%s,"throttled":%s,"firefox_running":%s}\n' \
    "$(date +%s)" "$disk_free" "$inode_free" "$root_read_only" "$temperature" "$throttled" "$firefox_running" >"$tmp"
  chmod 0644 "$tmp"
  mv -f "$tmp" "$output_file"
  sleep 30
done
