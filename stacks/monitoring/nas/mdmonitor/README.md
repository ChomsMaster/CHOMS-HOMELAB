# NAS mdraid monitoring

This block replaces only the two vendor `ExecStart` commands through systemd
drop-ins. It sends mdadm events to local syslog/journal and deliberately does
not configure email, SMTP, array operations or storage changes. The vendor
unit definitions remain installed and the oneshot unit's `AUTOSCAN` condition
is inherited unchanged.

Validate without changing the NAS:

```bash
./install.sh plan
```

Apply interactively on the NAS from this directory:

```bash
sudo ./install.sh apply
```

The installer refuses to overwrite an existing drop-in. Before application,
both target files must be absent and the array must be active, complete and
idle. After application, verify the effective commands, both unit results,
local journal delivery and array health before committing this change.

The initial deployment briefly replaced the vendor oneshot command directly.
If and only if that exact known override is installed, reconcile it while
preserving the vendor `AUTOSCAN` behavior:

```bash
sudo ./install.sh reconcile-oneshot
```

This mode restores `EnvironmentFile=-/etc/default/mdadm`, keeps execution
conditional on `AUTOSCAN=true`, and adds only `--syslog`. It backs up the
previous drop-in under `/run`, restores it automatically on failure, and
removes the runtime backup after success.

Rollback removes only these two installed drop-ins, reloads systemd and
restarts the vendor monitor:

```bash
sudo rm /etc/systemd/system/mdmonitor.service.d/override.conf
sudo rm /etc/systemd/system/mdmonitor-oneshot.service.d/override.conf
sudo systemctl daemon-reload
sudo systemctl restart mdmonitor.service
sudo systemctl start mdmonitor-oneshot.service
```

External alert delivery remains pending integration with Alertmanager. Local
syslog/journal restores monitoring visibility but does not provide an external
notification path by itself.
