# CHOMS-NODE-02

## Overview

  Property           Value
  ------------------ ------------------------------
  Hostname           choms-node-02
  Operating System   Debian GNU/Linux 13 (trixie)
  Kernel             6.12.95+deb13-amd64
  Architecture       x86_64
  Vendor             Lenovo
  Model              ThinkCentre M710q
  IP Address         192.168.1.172

------------------------------------------------------------------------

# Hardware

-   Lenovo ThinkCentre M710q
-   Architecture: x86_64

## Storage

  Device          Size Purpose
  ----------- -------- --------------------
  NVMe          \~1 TB Operating System
  SATA Disk     \~1 TB Local node storage

------------------------------------------------------------------------

# Storage Mounts

  Mount                  Source                         Protocol
  ---------------------- ------------------------------ ----------
  `/mnt/choms-media`     `192.168.1.167:/srv/media`     NFSv4.2
  `/mnt/choms-storage`   `192.168.1.167:/srv/storage`   NFSv4.2
  `/mnt/choms-local`     `/dev/sda1`                    ext4

------------------------------------------------------------------------

# Network

Primary interface:

``` text
enp0s31f6
```

Address:

``` text
192.168.1.172/24
```

------------------------------------------------------------------------

# Services

## Docker

  Container                 Purpose
  ------------------------- --------------
  `choms-jellyfin-node02`   Media server
  `choms-postgres`          PostgreSQL
  `choms-redis`             Redis

## Jellyfin

Container:

``` text
choms-jellyfin-node02
```

Port:

``` text
8096/tcp
```

Media:

``` text
/media -> /mnt/choms-media
```

## CHOMS Controller

Service:

``` text
choms-controller.service
```

Health:

``` text
http://127.0.0.1:8000/health
```

------------------------------------------------------------------------

# Firewall

Allowed:

-   SSH
-   Controller API from node 01

``` text
192.168.1.138 -> 192.168.1.172:8000
```

------------------------------------------------------------------------

# Validation

Completed:

-   Docker restored after reboot.
-   NFS mounts available.
-   Jellyfin media access validated.
-   CHOMS Controller operational.

------------------------------------------------------------------------

# Notes

Node 02 is ready for production-like workloads inside CHOMS
infrastructure.
