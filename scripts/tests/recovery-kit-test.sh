#!/usr/bin/env bash
# Synthetic harness only: no persistent fixture inputs or cryptographic material.
set +x
set -euo pipefail
umask 077
work=$(mktemp -d)
cleanup() { rm -rf -- "$work"; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
python3 -I -B "$script_dir/test_recovery_kit.py" "$work"
