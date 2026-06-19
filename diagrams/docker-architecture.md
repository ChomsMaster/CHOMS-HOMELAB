# Docker Architecture

```mermaid
flowchart TD
    Host[Debian 13 Host]
    Docker[Docker Engine]

    Nginx[choms-nginx<br/>nginx:stable-alpine<br/>Port 8080]
    Pihole[pihole<br/>pihole/pihole:latest<br/>Ports 53, 8081]
    Postgres[choms-postgres<br/>postgres:17<br/>127.0.0.1:5432]

    Data[/data<br/>Persistent Storage]
    Repo[/data/projects/choms-homelab/docker<br/>Compose Files]
 
    Host --> Docker
    Docker --> Nginx
    Docker --> Pihole
    Docker --> Postgres

    Nginx --> Data
    Pihole --> Opt
    Postgres --> Data

