# Removable USB Policy

## Current behavior

Debian Server minimal does not auto-mount arbitrary USB drives.

A USB disk appears in `lsblk`, but it does not become accessible until mounted manually or configured in `/etc/fstab`.

## Security decision

- Do not auto-mount arbitrary USB devices.
- Do not run desktop automounters on servers.
- Only trusted disks identified by UUID should auto-mount.

## Trusted disk pattern

Example:

```text
UUID=1CBB-DB78 /media/ssd-media exfat defaults,nofail,uid=1000,gid=1000,umask=0022 0 0
```

This mounts only that disk, regardless of which USB port it is connected to.

## Safe removal

Check mount:

```bash
lsblk -o NAME,MOUNTPOINT
mount | grep sd
```

Unmount:

```bash
sudo umount /dev/sdX1
```

If busy:

```bash
sudo fuser -vm /mount/path
sudo lsof +D /mount/path
```

Kill stuck processes only when safe:

```bash
sudo kill <PID>
# if required
sudo kill -9 <PID>
```
