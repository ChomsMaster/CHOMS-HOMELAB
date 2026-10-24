#!/bin/bash
set -euo pipefail

service="${1:-}"
shift || true

if [ -z "$service" ]; then
  echo "Usage: choms logs <service> [--tail=100] [-f]"
  exit 1
fi

/data/projects/choms-homelab/tools/commands/compose.sh logs "$service" "$@"
