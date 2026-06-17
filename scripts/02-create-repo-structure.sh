#!/bin/bash

set -e

echo "=== Creating repository structure ==="

mkdir -p docs
mkdir -p assets
mkdir -p diagrams
mkdir -p docker
mkdir -p scripts

touch assets/.gitkeep
touch diagrams/.gitkeep
touch docker/.gitkeep
touch scripts/.gitkeep

touch CHANGELOG.md
touch LICENSE
touch .gitignore

echo "=== Repository structure ready ==="
