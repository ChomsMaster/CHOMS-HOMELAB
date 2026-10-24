# NAS, node and storage monitoring

## Architecture

The locked `choms-monitoring` kube-prometheus-stack release scrapes one private
NAS target at `192.168.1.167:9100`. Relabeling fixes `instance=choms-nas` and
`role=nas`; the port is bound only to the NAS LAN address and has no public
route.

The NAS runs one digest-pinned node-exporter with only filesystem, diskstats,
hwmon, mdadm and textfile collectors. It is non-privileged, capability-free,
read-only and mounts no raw device or Docker socket. Its metrics script runs as
the existing unprivileged `chomsmaster` user. A persistent user timer refreshes
an atomic textfile every minute; `Linger=yes` starts that user manager after a
reboot without requiring an interactive login.

The textfile has one unlabeled series per summary: NFS service, `/srv/storage`
export, mdmonitor, RAID health and member counts, Scrutiny publication time,
eight-hour staleness, five-device count, and collection success. The script
reads Scrutiny's existing API and never runs `smartctl`.

## Alert coverage

CHOMS-specific `critical` rules cover persistent NAS exporter/textfile loss,
RAID degradation, NFS loss, inactive mdmonitor, stale Scrutiny collection,
urgent NAS filesystem/inode exhaustion, and temperatures above 90 C for ten
minutes. Kubernetes additions cover persistent NotReady/unreachable nodes,
Memory/Disk/PID pressure, and Pending/Lost PVCs.

Existing upstream critical rules continue to cover urgent Kubernetes node
filesystem/inode and PVC capacity exhaustion; they are not duplicated. CPU
high and predictive capacity warnings remain non-paging. Scrutiny 0.8.2 does
not expose an unambiguous Prometheus failure-prediction signal, so SMART health
remains visible in Scrutiny but is not translated into an alert. Kernel log
errors also remain outside this block.

## Operation and updates

From the repository root:

```bash
stacks/monitoring/nas/node-exporter/install.sh plan
stacks/kubernetes/monitoring/test-actionable-storage-rules.sh
```

Review the locked Helm server dry-run and persistent diff before applying.
The only expected persistent objects are the Prometheus resource, generated
additional-scrape Secret, and CHOMS PrometheusRule. Deploy the NAS block before
the targeted atomic `choms-monitoring` upgrade.

For a controlled notification check, use
`test-actionable-notification.sh start`, confirm the Telegram FIRING, then run
`test-actionable-notification.sh stop` and confirm RESOLVED. The helper only
creates and removes `choms_monitoring_synthetic_test`; never test by changing
RAID, NFS, mounts, filesystem usage or SMART state.

## Recovery

On a clean NAS, first confirm the declared status sources and obtain explicit
authorization for `sudo loginctl enable-linger chomsmaster`. Then run the NAS
plan/apply workflow. Validate the timer's next invocation, textfile age,
private listener, exporter health and Prometheus target before restoring the
Helm configuration. Rollback removes only the managed exporter, user units and
textfile; it does not modify NFS, mdraid, Scrutiny or disks.
