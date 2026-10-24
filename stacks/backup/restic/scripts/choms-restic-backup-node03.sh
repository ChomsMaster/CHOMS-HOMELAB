#!/usr/bin/env bash
# The public scope declares no application data backup on this destination node.
# Fail closed instead of reporting a backup that did not run.
set -euo pipefail
printf '%s\n' 'No public node-03 application backup scope is configured; no action performed.' >&2
exit 78
