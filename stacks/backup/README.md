# CHOMS Backup Automation

## Purpose

This directory contains the versioned automation used to protect the CHOMS
Kubernetes platform and Nextcloud data.

Backup data, credentials and SSH private keys are not stored in Git.

## Architecture

Two complementary backup paths are used.

### Kubernetes runtime and databases

`choms-node-01` creates a local backup under:

    /data/backups/kubernetes

The backup includes:

- PostgreSQL logical dump.
- MariaDB logical dump.
- Redis RDB dump.
- Kubernetes runtime inventory without Secret objects.
- Helm release inventory.
- Checksums and metadata.
- Non-sensitive K3s configuration when readable.

The validated backup is copied to the NAS through:

    /mnt/choms-backups/kubernetes

### Nextcloud consistent snapshot

`choms-node-01` creates a MariaDB dump and temporarily enables Nextcloud
maintenance mode.

The NAS then creates an XFS reflink snapshot containing:

- Nextcloud data.
- Nextcloud configuration.
- Custom applications.
- Themes.
- MariaDB dump.
- Checksums and metadata.

Nextcloud snapshots are stored under:

    /srv/storage/backups/homelab/nextcloud

## Retention

Both backup paths use the following GFS policy:

| Tier | Retention |
|---|---:|
| Daily | 7 |
| Weekly | 8 |
| Monthly | 12 |
| Yearly | 5 |

## Schedule

| Host | Timer | Approximate time |
|---|---|---:|
| `choms-node-01` | `choms-kubernetes-backup.timer` | 03:15 |
| `choms-node-01` | `choms-backup-nas-sync.timer` | 03:30 |
| `choms-node-01` | `choms-backup-gfs-retention.timer` | 03:40 |
| `choms-node-01` | `choms-nextcloud-data-backup.timer` | 04:10 |
| `choms-nas` | `choms-nextcloud-gfs.timer` | 04:25 |

Timers use a randomized delay of up to five minutes.

## Prerequisites

On `choms-node-01`:

- K3s, kubectl and Helm are functional.
- `/data` is an independent local filesystem.
- `/mnt/choms-backups` mounts the NAS backup export.
- `/mnt/choms-storage` mounts the complete NAS storage export.
- The NAS SSH host key is present in the user known-hosts file.
- `/home/chomsmaster/.ssh/choms_nas_backup` exists with secure permissions.

On `choms-nas`:

- `/srv/storage` is mounted on XFS.
- XFS reflink support is available.
- The restricted sudoers policy is installed.
- The Nextcloud control scripts are owned by root and are not user-writable.

## Security

- Kubernetes Secret objects are excluded from runtime exports.
- Credentials are read at runtime from Kubernetes or container environments.
- Backup directories and database dumps use restrictive permissions.
- SSH private keys and backup contents must never be committed.
- Only the Nextcloud backup control entry point receives passwordless sudo.

## Important Limitation

NAS reflink snapshots protect against logical deletion and application-level
mistakes, but they reside on the same RAID filesystem as the live data.

They are not protection against complete NAS loss. An encrypted independent
or off-site copy remains required for full disaster recovery.

## Restore Test

Run the controlled Nextcloud recovery test on `choms-node-01`:

    sudo /usr/local/sbin/choms-nextcloud-restore-test.sh

The test:

1. Validates the latest Nextcloud snapshot.
2. Creates an XFS reflink clone of the protected files.
3. Exports and validates the MariaDB dump.
4. Starts a temporary MariaDB Pod using the immutable image ID currently
   running in the cluster.
5. Restores the dump into an isolated database.
6. Validates table, user and file-cache counts.
7. Deletes the temporary Pod and dump.

Production Nextcloud and MariaDB are not modified.

Remove temporary file clones after recording the result:

    sudo /usr/local/sbin/choms-nextcloud-backup-control.sh restore-test-clean

## Last Recovery Validation

Validation completed on 2026-08-14:

- Snapshot: `20260814-041500`
- MariaDB tables restored: 127
- Nextcloud users found: 2
- File-cache records found: 25083
- Temporary MariaDB Pod removed successfully
- Nextcloud maintenance mode remained disabled
- Nextcloud status endpoint remained healthy
- Production database was not modified

## Validation

A backup is considered valid only after:

1. Every expected artifact is non-empty.
2. `SHA256SUMS` validates successfully.
3. Database dump structure is verified.
4. A controlled restore test succeeds.
5. Application functionality is checked after restoration.
