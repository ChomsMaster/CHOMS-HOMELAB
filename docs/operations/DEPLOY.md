# CHOMS Deploy Operations

## List Available Stacks

    choms deploy

## Deploy Redis

    choms deploy redis

## Deploy PostgreSQL

    choms deploy postgres

## Verify PostgreSQL

    docker exec -it choms-postgres pg_isready -U choms -d choms_platform

## Verify Redis

    docker exec -it choms-redis redis-cli ping
