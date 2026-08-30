#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
HELPER="$ROOT/scripts/choms-restic-remote-check.sh"
work=$(mktemp -d)
cleanup() { rm -rf -- "$work"; }
trap cleanup EXIT HUP INT TERM

classify() {
  local helper=$1 target=$2 status
  if bash "$helper" classify-repository "$target" >/dev/null 2>&1; then
    status=0
  else
    status=$?
  fi
  case "$status" in
    0) echo EMPTY ;;
    10) echo RESTIC ;;
    20) echo UNKNOWN ;;
    *) echo ERROR ;;
  esac
}

expect_classification() {
  local expected=$1 helper=$2 target=$3 actual
  actual=$(classify "$helper" "$target")
  test "$actual" = "$expected" || {
    echo "ERROR: expected $expected, got $actual for $target" >&2
    exit 1
  }
}

mkdir "$work/empty"
expect_classification EMPTY "$HELPER" "$work/empty"

mkdir -p "$work/restic"/{data,index,keys,locks,snapshots}
install -m 0600 /dev/null "$work/restic/config"
expect_classification RESTIC "$HELPER" "$work/restic"

mkdir "$work/unknown"
mkdir "$work/unknown/unrelated"
expect_classification UNKNOWN "$HELPER" "$work/unknown"

expect_classification ERROR "$work/missing-helper.sh" "$work/empty"
echo 'repository_classification_tests=passed EMPTY RESTIC UNKNOWN ERROR'
