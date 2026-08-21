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
| Kubernetes | `scrutiny-logical-backup` CronJob | 02:45 Europe/Madrid |

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

## Scrutiny cold bootstrap backup

The Scrutiny server has a manual cold-backup procedure for use before recovery
or security work:

    /usr/local/sbin/choms-scrutiny-bootstrap-backup.sh

It performs a preflight before downtime, scales only the Scrutiny server to
zero, mounts its configuration and InfluxDB host paths read-only, and publishes
the validated copy atomically under the existing NAS backup mount. The backup
tree is mode `0700` because InfluxDB 2.2 metadata contains authentication
material. The procedure restores the original replica count through a trap and
enforces a sub-ten-minute interruption.

This is a manual bootstrap copy, not the RPO 24-hour recurring backup. It does
not create or recover an InfluxDB token and must not be synchronized to a less
restricted destination.

### InfluxDB backup authorization contract

The one-time recovery prerequisite uses the official
[`influxd recovery auth create-operator`](https://docs.influxdata.com/influxdb/v2/reference/cli/influxd/recovery/auth/create-operator/)
command with InfluxDB stopped. Its dedicated authorization exists only for the
future official backup/restore workflow and is stored in the runtime Secret
`monitoring/scrutiny-backup-influx-operator` with exactly these keys:

- `token`
- `authorization-id`

Neither value belongs in Git, local environment files, command arguments,
logs, Pod specifications or retained evidence. Consumers must use
`secretKeyRef` and disable ServiceAccount-token automount when they do not need
the Kubernetes API. Revocation must authenticate with this same authorization,
delete its InfluxDB authorization first, verify that authentication then fails,
and only afterwards delete the Kubernetes Secret.

The authorization bootstrap does not implement the recurring RPO-24-hour
backup and does not authorize a production restore or `SEC-003` hardening.

## Scrutiny recurring logical backup

[`backup.yaml`](../kubernetes/scrutiny/backup.yaml) declares an internal-only
InfluxDB Service, the backup script ConfigMap and a daily CronJob. The CronJob
uses the official InfluxDB 2.2.0 image, whose bundled CLI is 2.3.0, and the
pinned Python image used by the established restore tooling. It performs:

- official online `influx backup` using `INFLUX_TOKEN` from `secretKeyRef`;
- transactional SQLite backup through Python's `sqlite3_backup` API while the
  production directory is mounted read-only;
- mode-0700 staging, a cross-run lock, file-size and SHA-256 manifests;
- atomic directory publication and a `latest` pointer;
- GFS retention of 7 daily, 8 weekly, 12 monthly and 5 yearly copies.

Logical copies live under `/mnt/choms-backups/scrutiny/logical`. The separate
bootstrap tree is outside retention scope and must never be removed by this
workflow. The Job has a 20-minute deadline, forbids overlap, retains one
successful and one failed history entry, mounts no ServiceAccount token, and
has no privileged or host-namespace access.

The existing NAS and source host paths require UID/GID 0. A non-root preflight
could not traverse the protected mode-0700 paths. The containers remain
non-privileged with all capabilities dropped, no privilege escalation,
`RuntimeDefault` seccomp and read-only root filesystems.

Run the isolated logical restore validation with:

    /usr/local/sbin/choms-scrutiny-logical-restore-test.sh

The test verifies both checksum manifests, restores SQLite into a separate
1 GiB `emptyDir`, runs `influx restore --full` against a fresh isolated
InfluxDB 2.2.0 instance, validates TSM, series and any restored WAL offline,
then starts the pinned Scrutiny 0.8.2 image. It creates no Service, route,
hostPort or collector endpoint and removes the Pod and restored data on exit.

Validate the latest copy without production writes:

    /usr/local/sbin/choms-scrutiny-bootstrap-restore-test.sh

The restore test uses a separate 1 GiB `emptyDir`, validates checksums, SQLite
integrity, InfluxDB series/TSM/WAL/tombstone structures, and starts the pinned
Scrutiny 0.8.2 image with its embedded InfluxDB 2.2.0. It creates no Service,
route or collector endpoint and deletes the Pod and restored data on exit.

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

Scrutiny cold-bootstrap recovery validation completed on 2026-08-21:

- Cold copy published atomically to the restricted NAS destination.
- Production interruption completed well below the ten-minute limit.
- SQLite and InfluxDB offline integrity checks passed.
- Isolated InfluxDB 2.2.0 and Scrutiny 0.8.2 started healthy.
- Temporary Pods, Jobs and restored data were removed.
- Production Scrutiny, collectors and ingestion remained healthy.

Scrutiny logical-backup validation completed on 2026-08-22:

- One daily backup was published atomically with 17 files and valid checksums.
- SQLite online backup and isolated `integrity_check` passed.
- Full InfluxDB restore plus offline storage validation passed.
- Isolated InfluxDB 2.2.0 and Scrutiny 0.8.2 started healthy.
- GFS ran with no eligible weekly, monthly or yearly promotion and preserved
  the cold bootstrap checksums.
- The CronJob is active for 02:45 Europe/Madrid; no temporary resource, lock
  or partial copy remains.

## Validation

A backup is considered valid only after:

1. Every expected artifact is non-empty.
2. `SHA256SUMS` validates successfully.
3. Database dump structure is verified.
4. A controlled restore test succeeds.
5. Application functionality is checked after restoration.
