# ADR-003 - Storage Layout

## Status

Accepted

## Decision

Separate operating system and project data.

System:

/

Data:

/data

## Rationale

- Easier backups
- Easier migrations
- Better disaster recovery

## Consequences

Application data must never be stored inside the operating system partition.
