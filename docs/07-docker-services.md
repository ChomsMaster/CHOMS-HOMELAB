# Services

## Docker services

Current running services:

- choms-nginx: test web service
- pihole: DNS filtering
- choms-postgres: PostgreSQL database

## PostgreSQL

- Version: PostgreSQL 17
- Container: choms-postgres
- Database: choms_lab
- User: choms_admin
- Binding: 127.0.0.1:5432
- Data path: /data/postgres

PostgreSQL is intentionally bound only to localhost for security.
