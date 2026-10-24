#!/bin/bash
set -euo pipefail

cd /data/projects/choms-homelab

echo "CHOMS-HOMELAB"
echo "============="
echo "Branch : $(git branch --show-current)"
echo "Commit : $(git rev-parse --short HEAD)"
echo "Date   : $(git log -1 --format=%cd --date=short)"
echo "Kernel : $(uname -r)"
