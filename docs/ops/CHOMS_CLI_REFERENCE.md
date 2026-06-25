# CHOMS CLI Reference

## Purpose

`choms` is the operational CLI for CHOMS-HOMELAB.

It centralizes common operational tasks so the administrator does not need to remember raw Docker, systemd, Git and service commands.

## Core Commands

```bash
choms help
choms health
choms status
choms doctor
choms version
choms urls
```

## Docker and Compose

```bash
choms compose ps
choms compose config
choms compose up -d
choms compose logs <service>
choms compose restart <service>
```

## Services

```bash
choms service list
choms service status
choms service restart <service>
choms service logs <service>
choms service shell <service>
```

## Shortcuts

```bash
choms logs <service>
choms restart <service>
```

## Operations

```bash
choms update
choms vault
choms vault list
choms vault show <service>
```

## Infrastructure Status

```bash
choms storage
choms shares
choms docker
choms services
choms monitoring
```

## CLI Structure

```text
tools/choms
tools/commands/
```

Each command is implemented as a separate script under `tools/commands/`.

This keeps the CLI modular and ready to grow.

## Design Principle

CHOMS CLI should behave like an operational control plane for the homelab.

Instead of remembering low-level commands, the administrator should be able to use:

```bash
choms health
choms service list
choms restart grafana
choms logs traefik
```

## Future Commands

Planned for Phase 2:

```bash
choms disks
choms backup
choms restore
choms snapshot
choms verify
```
