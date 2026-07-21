# Disaster Recovery

## Objective

Recover CHOMS-HOMELAB after a critical failure.

## Scenario 1

System SSD failure

Recovery:

- Replace SSD
- Install Debian
- Clone repository
- Restore configuration
- Restore backups
- Validate with CHOMS Doctor

## Scenario 2

Data SSD failure

Recovery:

- Replace SSD
- Restore /data
- Restore Docker data
- Restore PostgreSQL backup

## Scenario 3

Docker failure

Recovery:

- Install Docker
- Restore compose files
- Deploy services
- Validate containers

## Scenario 4

WireGuard failure

Recovery:

- Restore configuration
- Restart service
- Validate VPN

## Scenario 5

Complete power outage

Expected behaviour:

- BIOS powers on automatically.
- Debian boots.
- Docker starts.
- Services recover automatically.

Validation:

Run CHOMS Doctor.
