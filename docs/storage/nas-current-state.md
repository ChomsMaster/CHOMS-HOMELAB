# NAS Current State

## Host

- Hostname: `choms-nas`
- LAN IP: `192.168.1.167`
- OS: Debian

## Current disks and arrays

| Mount | Backing | Approx size | Filesystem | Risk |
|---|---|---:|---|---|
| `/` | Kingston SSD | 120 GB | ext4 | Normal system disk |
| `/srv/media` | RAID0 2×2 TB | 3.6 TB | ext4 | No redundancy |
| `/srv/storage` | RAID0 2×3 TB | 5.5 TB | ext4 | No redundancy |

## Important warning

The NAS currently uses RAID0 arrays. This provides capacity/performance, not protection. If one disk in an array fails, the array is lost.

This is acceptable only as a temporary/transitional setup while CHOMS is being built.

## NFS export

Current export:

```text
/srv/media 192.168.1.0/24(rw,sync,no_subtree_check,root_squash)
```

Node-01 mounts it at:

```text
/mnt/choms-media
```

Movies are available at:

```text
/mnt/choms-media/Movies
```

## Next storage work

- Decide final disk strategy.
- SMART audit all disks.
- Plan real backup target.
- Decide if future NAS uses Debian + mdadm/ZFS or TrueNAS.
- Add backup verification.
- Document restore procedures.
