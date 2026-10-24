#!/bin/bash

log() {
    echo
    echo "================================================="
    echo "$1"
    echo "================================================="
}

success() {
    echo "✓ $1"
}

warning() {
    echo "! $1"
}

die() {
    echo "ERROR: $1"
    exit 1
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

docker_container_exists() {
    docker ps -a --format '{{.Names}}' | grep -qx "$1"
}
