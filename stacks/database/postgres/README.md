# CHOMS PostgreSQL Stack

Role: Database service for CHOMS Platform.

## Node

Application Node

- Host: choms-node-02
- Data path: /data/docker/postgres
- Stack path: /data/docker/stacks/database/postgres
- Network: choms-database

## Service

- Image: postgres:17
- Container: choms-postgres
- Database: choms_platform
- Port: 127.0.0.1:5432

## Deploy

    ./deploy.sh

## Health Check

    docker exec -it choms-postgres pg_isready -U choms -d choms_platform

## Version

    docker exec -it choms-postgres psql -U choms -d choms_platform -c "SELECT version();"

