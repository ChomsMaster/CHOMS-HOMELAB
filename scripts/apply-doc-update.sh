#!/usr/bin/env bash
set -euo pipefail

if [ ! -d .git ]; then
  echo "ERROR: run this from the CHOMS-HOMELAB repository root."
  exit 1
fi

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

rsync -av "$SOURCE_DIR/" ./

echo

echo "Documentation update copied. Review with:"
echo "  git status"
echo "  git diff -- CHOMS-HOMELAB_MASTER_CONTEXT.md PROJECT_STATUS.md SESSION_STATE.md ROADMAP.md docs/"
