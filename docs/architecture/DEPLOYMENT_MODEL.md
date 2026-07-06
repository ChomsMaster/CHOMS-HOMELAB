# CHOMS Deployment Model

## Principle

The Git repository is the Single Source of Truth.

Runtime directories must not be edited as source.

## Repository

    /data/projects/CHOMS-HOMELAB

Contains:

- stacks
- scripts
- tools
- docs
- configuration templates

## Runtime

    /data/docker

Contains deployed runtime artifacts.

Runtime may contain local `.env` files that are not versioned.

## Deployment Flow

    Git
      ↓
    stacks/<domain>/<stack>
      ↓
    choms deploy <stack>
      ↓
    /data/docker/stacks/<domain>/<stack>
      ↓
    docker compose up -d

## Environment Files

Versioned:

    .env.example

Runtime-only:

    .env

The deploy command must not overwrite `.env`.

## Rule

Do not manually maintain files inside `/data/docker/stacks` as source.
