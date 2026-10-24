#!/bin/bash
set -euo pipefail

service="${1:-}"

if [ -z "$service" ]; then
  echo "Usage: choms restart <service>"
  exit 1
fi

/data/projects/choms-homelab/tools/commands/compose.sh restart "$service"
