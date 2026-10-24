# Raspberry Pi external monitor

This phase runs one lightweight container on the US Raspberry Pi 3. It checks
the main endpoint, one public application (including Nextcloud's stable login
redirect) and one Authelia-protected route for DNS, TLS, expected HTTP response
and latency. A restricted host helper reports
microSD space/inodes, read-only root state, temperature, throttling when
available, and whether the existing `firefox-web` container is running.

The helper avoids mounting `docker.sock` in the monitor. It performs only an
exact-name, read-only `docker inspect`; the monitor is unprivileged, drops all
capabilities, has a read-only root, and is limited to 48 MiB and 0.20 CPU.
The RP3 kernel reports that it cannot enforce Docker's declared memory limit.
The declaration remains the desired constraint, but operators must account for
this kernel limitation; changing the kernel or Docker globally is out of scope.

## Operations

From `node-dev-01`, synchronize this directory to
`/home/chomsmaster/choms-external-monitor`, install/enable the supplied unit
with `systemctl --user`, then run `./install-secrets-and-deploy.sh`. The script reads credentials
without echo, transfers files with mode 0600, builds on ARMv7, starts only the
monitor, sends controlled FIRING/RESOLVED messages, and records confirmation.
Rerun the same script to rotate either credential.

Alert state is stored in the persistent local `state` directory. Three
consecutive failures produce one FIRING; no repeats are sent during the
incident; recovery produces one RESOLVED. Restore by synchronizing the
directory, restoring the credential files interactively, enabling the host
helper and running Compose. Losing the state directory can cause an existing
incident to notify again.

To add a remote check, append one item to `checks` in `config.json` and redeploy.
Future Kubernetes summary, NFS/PVC and SMART inputs should be added as new
read-only provider files under `host-status` and evaluated by this same process;
they must not create another monitoring container or add broad credentials.

## Active power incident

`rp3-local` intentionally remains firing for `throttled=0x50005`. Firmware bits
show current and historical undervoltage and throttling, not a temperature
incident. Replace the supply with a known-good regulated 5.1 V / 2.5 A unit and
use a short, low-resistance micro-USB cable. Do not reboot until power is
stable. The current bits should disappear and RESOLVED should be sent
automatically; historical bits clear only after a later controlled reboot.
