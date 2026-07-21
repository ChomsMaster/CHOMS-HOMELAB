# CHOMS Node Roles

## Edge Node

Host:

    choms-node-01

Responsibilities:

- Reverse proxy
- VPN
- DDNS
- Authentication
- Monitoring frontend
- DNS services

## Application Node

Host:

    choms-node-02

Responsibilities:

- PostgreSQL
- Redis
- Nextcloud
- ShiftCore
- Application services
- Worker services

## Storage Node

Host:

    choms-nas

Responsibilities:

- RAID storage
- NFS
- Media storage
- Backups
- File services
