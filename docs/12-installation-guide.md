# CHOMS-HOMELAB Installation Guide

## Objective

Rebuild the complete CHOMS-HOMELAB infrastructure from scratch.

## Hardware

- Mini PC
- System SSD
- Data SSD
- Ethernet connection

## Operating System

- Debian 13

## Installation Order

1. Install Debian 13
2. Update the operating system
3. Install Git
4. Clone CHOMS-HOMELAB repository
5. Execute installation scripts in order

Scripts:

01-install-base-tools.sh

02-create-server-structure.sh

03-install-docker.sh

04-setup-firewall.sh

05-setup-storage.sh

06-install-wireguard.sh

07-deploy-nginx.sh

08-deploy-postgresql.sh

09-deploy-pihole.sh

10-backup-system.sh

11-update-system.sh

12-restore-server.sh

## Validation

Run CHOMS Doctor.

Infrastructure must report healthy status before production.
