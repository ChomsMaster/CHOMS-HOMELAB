#!/usr/bin/env bash
# Local validation only. Never executes repository deployment scripts.
set -uo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root" || exit 1
exec python3 scripts/validation_inputs.py "$@"
