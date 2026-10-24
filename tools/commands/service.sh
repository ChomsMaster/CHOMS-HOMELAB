#!/bin/bash
set -euo pipefail

cmd="${1:-help}"
service="${2:-}"

case "$cmd" in
  list)
    /data/projects/choms-homelab/tools/commands/compose.sh config --services
    ;;

  status|ps)
    /data/projects/choms-homelab/tools/commands/compose.sh ps
    ;;

  restart)
    [ -n "$service" ] || { echo "Usage: choms service restart <service>"; exit 1; }
    /data/projects/choms-homelab/tools/commands/compose.sh restart "$service"
    ;;

  logs)
    [ -n "$service" ] || { echo "Usage: choms service logs <service>"; exit 1; }
    shift 2 || true
    /data/projects/choms-homelab/tools/commands/compose.sh logs "$service" "$@"
    ;;

  shell)
    [ -n "$service" ] || { echo "Usage: choms service shell <service>"; exit 1; }
    /data/projects/choms-homelab/tools/commands/compose.sh exec "$service" sh
    ;;

  help|*)
    echo "Usage:"
    echo "  choms service list"
    echo "  choms service status"
    echo "  choms service restart <service>"
    echo "  choms service logs <service> [--tail=100] [-f]"
    echo "  choms service shell <service>"
    ;;
esac
