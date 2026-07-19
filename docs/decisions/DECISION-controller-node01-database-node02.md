# Decision: CHOMS Controller placement

## Context

CHOMS Controller was initially deployed on Node 02 during application service validation.

The target architecture separates control plane and workload nodes.

## Decision

CHOMS Controller runs on:

- Node: choms-node-01
- IP: 192.168.1.138
- Service: choms-controller.service

PostgreSQL runs on:

- Node: choms-node-02
- IP: 192.168.1.172
- Container: choms-postgres

## Database Connectivity

Controller connects using:

choms-node-02:5432

The database is no longer bound only to localhost.

## Reason

This separation allows:

- Centralized orchestration
- Independent compute nodes
- Future node registration
- Better CHOMS cluster architecture

## Status

Accepted.

