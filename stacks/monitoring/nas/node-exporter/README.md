# CHOMS NAS node-exporter

This block adds one private node-exporter target for `choms-nas`. It uses the
same pinned exporter bytes as Kubernetes and listens only on the NAS LAN
address. The container is non-privileged, read-only, capability-free and has
no raw-device or Docker socket access. Only filesystem, diskstats, hwmon,
mdadm and textfile collectors are enabled.

The unprivileged `chomsmaster` user timer atomically publishes low-cardinality
summaries once per minute: NFS service/export state, mdmonitor state, md0
member state, and Scrutiny publication freshness/device count. All host
sources are world-readable status files or service state. Scrutiny is queried
through its existing API; the script never invokes `smartctl` and emits no
device label, serial or SMART attribute. A publication older than eight hours
is stale.

Run `./install.sh plan` before `./install.sh apply`. The preflight refuses an
unmanaged existing port, container, unit, script or deployment directory and
requires `Linger=yes` for reboot persistence. Enable linger once as an
authorized NAS administrator with `sudo loginctl enable-linger chomsmaster`.
Rollback stops only the new exporter, disables its timer and removes its
installed files.

Updates must keep the image digest locked, run the plan and monitoring rule
tests, review the Helm diff, and deploy NAS then Helm in that order. Recovery
is `./install.sh apply` on a clean NAS after confirming the same source paths.

Pending coverage: kernel log errors are not exported. Scrutiny 0.8.2 does not
provide a sufficiently unambiguous Prometheus-compatible failed/predicted
failure signal, so SMART health and detailed attributes remain in Scrutiny and
are deliberately not translated or duplicated.
