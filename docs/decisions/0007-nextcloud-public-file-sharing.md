# ADR 0007: Nextcloud provides public client file sharing

- **Status:** accepted

## Context

Client file delivery needs authenticated controls, expiration, download
integrity, and application-level auditing. Exposing SMB, NFS, or the NAS would
bypass the platform edge and broaden infrastructure exposure.

## Decision

Use Nextcloud for public client file sharing. Require a password, enforce a
maximum seven-day expiration, default to read-only download, and disable public
upload. Send links and passwords through separate channels. Do not expose SMB,
NFS, or the NAS publicly for this purpose.

## Consequences

Nextcloud availability and backup become part of the delivery path. Policy is
maintained through the versioned idempotent script and validated with isolated
test data, never real user content.

## Evidence

- [`NEXTCLOUD_SHARING.md`](../operations/NEXTCLOUD_SHARING.md)
- [`configure-nextcloud-sharing.sh`](../../stacks/kubernetes/apps/configure-nextcloud-sharing.sh)
- [`WORKLOG.md`](../context/WORKLOG.md)
