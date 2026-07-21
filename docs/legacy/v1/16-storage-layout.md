# Storage Layout

Current storage design:

| Device | Mount | Purpose |
|---|---|---|
| M.2 128GB | / | Debian system |
| SSD 960GB | /data | Main persistent data |
| SSD 256GB exFAT | /media/ssd-media | Portable media / TV |
| microSD 2TB | not trusted | Temporary only |

## Main Data Disk

/data contains:

- backups
- docker
- media
- nextcloud
- pihole
- postgres
- projects
- storage
- websites

## Principle

System and data are separated. Debian lives on the M.2. Persistent application and user data live under /data.
