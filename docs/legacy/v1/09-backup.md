# Backup Strategy

## Objective

The backup strategy is designed to minimize downtime and data loss while keeping the infrastructure simple and maintainable.

Backups are organized into two categories:

* Configuration backups
* Data backups

---

## Configuration Backups

Configuration backups include all files required to rebuild the infrastructure.

Current backup targets:

* Docker Compose files
* WireGuard configuration
* UFW configuration
* Fail2ban configuration
* Nginx configuration
* System configuration
* Project documentation

---

## Data Backups

Application data is stored separately from the operating system whenever possible.

Current data locations include:

* PostgreSQL volumes
* Pi-hole configuration
* Docker volumes
* Future Nextcloud data

---

## Backup Storage

Current storage:

* Secondary SSD mounted on `/data`
* `/data/backups`

Future improvements:

* External USB drive
* Encrypted remote backup
* Scheduled backup automation

---

## Recovery Strategy

Infrastructure recovery follows these steps:

1. Install Debian.
2. Install Docker.
3. Restore project repository.
4. Restore Docker volumes.
5. Start containers.
6. Verify network connectivity.
7. Validate services.

This approach allows the infrastructure to be rebuilt quickly on replacement hardware.

---

## Future Improvements

Planned enhancements include:

* Automated nightly backups
* Database dumps
* Incremental backups
* Backup verification
* Backup monitoring
* Off-site encrypted copies

