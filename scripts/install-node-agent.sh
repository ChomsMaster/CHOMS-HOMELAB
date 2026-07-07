#!/usr/bin/env bash
set -euo pipefail

ROLE="${1:-}"
SITE="${CHOMS_SITE:-madrid}"
DOMAIN="${CHOMS_DOMAIN:-chomsmaster.com}"

if [[ $EUID -ne 0 ]]; then
  echo "ERROR: run with sudo."
  exit 1
fi

if [[ -z "$ROLE" ]]; then
  echo "Usage: sudo ./scripts/install-node-agent.sh <edge|application|storage|compute>"
  exit 1
fi

mkdir -p /opt/choms/agent /var/lib/choms/agent /var/log/choms

cp scripts/agent/choms-node-agent.sh /opt/choms/agent/choms-node-agent.sh
chmod +x /opt/choms/agent/choms-node-agent.sh

cp scripts/agent/choms-node-agent.service /etc/systemd/system/choms-node-agent.service
cp scripts/agent/choms-node-agent.timer /etc/systemd/system/choms-node-agent.timer

if [[ ! -f /opt/choms/node.yaml ]]; then
  NODE_ID="$(cat /etc/machine-id 2>/dev/null || uuidgen)"
  cat > /opt/choms/node.yaml <<NODE
node_id: "$NODE_ID"
hostname: "$(hostname)"
role: "$ROLE"
site: "$SITE"
domain: "$DOMAIN"
controller: "choms-node-01"
NODE
fi

systemctl daemon-reload
systemctl enable --now choms-node-agent.timer

echo "CHOMS Node Agent installed."
echo
cat /opt/choms/node.yaml
