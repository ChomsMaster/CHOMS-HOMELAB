#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="${CHOMS_BASE_DIR:-/data/projects/choms-homelab}"
RUNTIME_DIR="${CHOMS_RUNTIME_DIR:-/data/docker/stacks}"

STACK="${1:-}"

if [[ -z "$STACK" ]]; then
  echo "Usage: choms deploy <stack>"
  echo
  echo "Available stacks:"
  find "$BASE_DIR/stacks" -mindepth 2 -maxdepth 2 -type d | sed "s#$BASE_DIR/stacks/##" | sort
  exit 1
fi

SRC="$(find "$BASE_DIR/stacks" -mindepth 2 -maxdepth 2 -type d -name "$STACK" | head -1)"

if [[ -z "$SRC" ]]; then
  echo "ERROR: stack not found: $STACK"
  exit 1
fi

REL="${SRC#$BASE_DIR/stacks/}"
DST="$RUNTIME_DIR/$REL"

echo "=============================================="
echo " CHOMS Deploy"
echo "=============================================="
echo
echo "Stack:   $STACK"
echo "Source:  $SRC"
echo "Runtime: $DST"
echo

mkdir -p "$DST"
rsync -av --delete \
  --exclude ".env" \
  "$SRC/" "$DST/"

cd "$DST"

if [[ ! -f ".env" && -f ".env.example" ]]; then
  cp .env.example .env
  echo "Created runtime .env from .env.example"
fi

docker compose -f compose.yaml config >/tmp/choms-deploy-"$STACK".out
docker compose -f compose.yaml up -d

echo
echo "Deploy completed: $STACK"
