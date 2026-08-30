# Encrypted node-03 recovery copy

This block declares and operates the validated encrypted recovery checkpoint.
The repository is restricted to
`/mnt/choms-local/backups/choms-platforms-restic`; no other HDD entry is
modified. Node-01 and node-02 encrypt locally with Restic before SFTP transport.
Node-03 uses the same repository through its local path.

The completed checkpoint contains six hostname/type snapshot categories and
passed `restic check`, scope/exclusion validation and the 25 GiB guard. Its
validated aggregate is 1,242,635,604 logical bytes and 1,108,695,459 stored
bytes. The password and private keys are not stored in Git; external password
custody is mandatory.

Run the orchestrator as `chomsmaster`, never through sudo global:

```bash
stacks/backup/restic/deploy-encrypted-recovery.sh fingerprints
stacks/backup/restic/deploy-encrypted-recovery.sh deploy
stacks/backup/restic/deploy-encrypted-recovery.sh resume-initialize
stacks/backup/restic/deploy-encrypted-recovery.sh validate
stacks/backup/restic/finalize-encrypted-recovery.sh finalize
stacks/backup/restic/finalize-encrypted-recovery.sh validate
```

`fingerprints` scans only Ed25519 host keys, requires the three literal
out-of-band confirmations, installs only confirmed keys in the operator's
normal `known_hosts`, and exits successfully without administrative SSH.
`deploy` requires all three pinned identities to match fresh scans without
asking for confirmation again. It transfers root-free staging trees and then
runs the versioned `choms-restic-deploy-node01.sh`,
`choms-restic-deploy-node02.sh`, and `choms-restic-deploy-node03.sh` bundles.
Each bundle performs all privileged operations for its phase inside one
visible `ssh -t ... sudo <bundle>` session. Read-only queries remain
non-interactive BatchMode SSH. Existing recognized state is retained, while
conflicts or unknown destination content stop the run. `validate` invokes one
installed read-only validation bundle per node; it does not create, change or
delete backup resources.

`resume-initialize` is only for an interrupted prepared deployment whose
repository is still EMPTY; it resumes at the literal initialization gate
without repeating completed preparation. `finalize` runs the one-time Restic
check and aggregate scope validation, guards against `Persistent=true`
catch-up, and activates timers without manually starting a backup. The
finalizer's `validate` subcommand is unprivileged and read-only; it rechecks
metrics, timer waiting state, the node-03 validation report, bind mount and
sshd health without running Restic again.

The deployer does not use `sudo -S`, askpass, forwarded agents, `accept-new`,
disabled host-key checking, credentials on stdin, or monitoring Helm changes.

The `choms-restic` account uses UID/GID 980, home
`/var/lib/choms-restic`, shell `/usr/sbin/nologin`. Its independent chroot is
`/var/lib/choms-restic/chroot`; every ancestor is root-owned and not
group/other-writable. A versioned systemd bind mount exposes only the real
repository at `/choms-platforms-restic` inside that chroot. The mount requires
the existing `/mnt/choms-local` filesystem, persists through reboot, and is
validated before sshd reload or any backup timer enablement. The HDD mount
itself is never required to be root-owned and its owner/mode are not changed.
The repository remains `choms-restic:choms-restic 0700` at
`/mnt/choms-local/backups/choms-platforms-restic`.
Git stores the stable template as `systemd/choms-restic-repository.mount`.
Node-03 derives the installed basename exclusively with `systemd-escape
--path --suffix=mount /var/lib/choms-restic/chroot/choms-platforms-restic`;
the orchestrator rejects multiple lines, slashes and non-`.mount` results.
UID and GID 980 are used only if both are free; a collision is a hard stop.
Existing entries under `/mnt/choms-local` are preserved, and this workflow must
never format or partition `/dev/sda1` or modify `fstab`.

Each origin receives an independent Ed25519 key. Before known_hosts changes,
the node-03 Ed25519 host public key is read administratively, its SHA256
fingerprint shown to the operator, and explicit confirmation required. Root on
the origins uses a normal known_hosts file and `StrictHostKeyChecking=yes`.
Authorized keys use source-address `from=`, `restrict`, and forced internal
SFTP. They are stored root-controlled at
`/etc/ssh/authorized_keys/choms-restic` (`root:root 0644`) below a
`root:root 0755` directory, outside both the account home and chroot. The sshd
Match block selects that absolute path and also denies PTY, shell, tunnel and
forwarding. Deployment validates the staged fragment, effective sshd settings
and both origin SFTP probes before removing the obsolete home-relative
authorized-keys file.

The password is entered twice on each node with
`choms-restic-key-install.sh` directly through `/dev/tty`, with echo disabled.
The exact header is `RESTIC PASSWORD FOR choms-node-XX`; only the password and
its repetition disable terminal echo. Password confirmation is followed by the
visible literal gate `TYPE STORED`. Both `STORED` and
`INITIALIZE choms-platforms-restic` allow three attempts, accept only an exact
match, clear the rejected variable, and print
`confirmation_mismatch retry=N/3` before retrying. The value is atomically
stored only as `/etc/choms-backup/restic-password` mode 0600 and never transits
node-dev-01, arguments, environment, logs, or remote staging. If node-03 still
has an EMPTY repository, its password file is unconditionally replaced before
initialization so an interrupted or compromised pre-initialization value is
never reused. The bundle then unsets input variables, clears the terminal, and
asks the independent literal gate `TYPE INITIALIZE choms-platforms-restic`.
Node-03 initializes first; node-01 and node-02 subsequently receive the same
password through their own TTYs and prove equality only by opening that
repository. A mismatch stops without changing repository contents.

The resumable runtime sequence is split into bounded bundle phases:

1. Transfer declarative payloads without sudo and run one `prepare` bundle on
   node-01 and node-02. These reuse or create independent private keys locally
   and export only their public keys back through node-dev-01.
2. Build the source-restricted authorized-keys file locally from those public
   keys, transfer node-03's staging tree, and run its single `prepare` bundle.
   It reuses the partial chroot/mount/sshd state, installs the new password and
   initializes only after the separate literal confirmation.
3. Run one `execute` bundle on node-01, then node-02, then node-03. Origins
   install/verify their direct password, probe restricted SFTP and create only
   missing snapshots. Node-03 performs the final backup, `restic check`,
   snapshot assertions, sample restore and metrics validation.
4. Node-01 and node-02 finalizers wait without another sudo prompt. Only after
   node-03 reports global validation does node-dev-01 place a non-sensitive
   mode-0600 gate. Each finalizer independently rechecks repository, all
   expected snapshots and its metric before enabling its backup timer.

With every confirmation correct on its first attempt, a full deployment uses
six sudo prompts, six silent Restic password entries, three `STORED` inputs and
one initialization input: 16 prompts. Allowing the complete three-attempt
budget raises the strict maximum to 24. A resumed run with valid installed
state produces fewer prompts; it never produces more than two visible sudo
authentications per node. Re-running does not recreate matching users, private
keys, repositories, or existing hostname/tag snapshots.

If preparation completed but an EMPTY repository initialization was rejected,
use only `resume-initialize`. It transfers minimal resume payloads without
sudo, opens one node-03 sudo session for the initialization gate, then one
execution session on each origin. Node-03 completes its backup and global
validation through an already-started root finalizer, so no second node-03
authentication is needed. A root-only empty marker records successful password
installation without recording the password or a sensitive decision. Attempts
made before this marker existed require exactly one additional node-03 password
rotation; subsequent confirmation rejection resumes without another rotation.
Before every EMPTY initialization prompt the bundle displays the real path,
`repository_state=EMPTY`, and `password_input=finished`.
For the pre-marker interrupted state, the remaining first-attempt budget is
three sudo prompts, six silent password entries, three `STORED` inputs and one
initialization input: 13 prompts. With all confirmation retries used, the exact
remaining maximum is 21 prompts.

Monitoring mounts each node's Restic textfile directory read-only in
node-exporter and supplies two critical rules for persistent backup failure or
staleness. The controlled synthetic signal produced one confirmed FIRING and
RESOLVED, was removed, and ended inactive. The deployment never formats or
partitions storage, edits `fstab`, cleans locks, runs real `forget`, runs
`prune`, or touches other entries under `/mnt/choms-local`.

Timers are 05:00, 05:30, 06:00 and maintenance 06:30 Europe/Madrid. Local
`flock` and restic `--retry-lock 20m` serialize work after persistent catch-up.
No automatic unlock exists. Maintenance refuses any global lock and performs
only per-host/per-type `forget --dry-run` with 7 daily, 4 weekly and 6 monthly;
real forget and prune remain disabled pending separate review and approval.
The node-03 local backend runs as root to read protected sources, then restores
the required repository ownership after a successful write; remote origins
always write as the restricted SFTP owner.

The validated repository totals 1,242,635,604 logical bytes and 1,108,695,459
stored bytes. Every node has a hard 25 GiB logical-scope guard. Nextcloud
`data`, media, downloads, Colegio, personal or historical backups, Prometheus
TSDB, Loki, caches and the remainder of `/srv/storage` are outside the declared
source set.

This is an independent copy outside the NAS failure domain, but it remains on
a local node-03 HDD and is not offsite. Recovery requires that HDD, the
externally held repository password and a Restic version compatible with the
repository format. Losing the site, the HDD or the external password can make
this checkpoint unavailable; the off-site copy remains a separate roadmap
item.

The documented topology is a single K3s server and monitoring explicitly
disables kubeEtcd. The preflight found the three-file server database tree.
The node-01 script additionally requires `state.db`, rejects an etcd member or
external datastore/cluster-init declaration, and uses Python's transactional
SQLite backup API into `/run`. It never copies the live `server/db` tree.
