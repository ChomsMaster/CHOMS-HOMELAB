# Decision: Jellyfin startup dependency with remote NFS storage

## Context

CHOMS-NODE-02 runs Jellyfin as a Docker service.

The media library is not stored locally. Jellyfin consumes media from
the CHOMS storage node through NFS.

Storage details:

-   Storage node: 192.168.1.167
-   Export: /srv/media
-   Client mount: /mnt/choms-media
-   Protocol: NFSv4.2

During initial deployment, Jellyfin used automatic container restart:

restart: unless-stopped

This created a possible startup race condition:

1.  System boots.
2.  Docker starts.
3.  Jellyfin container starts.
4.  NFS mount is not ready.
5.  Jellyfin starts without guaranteed access to the media library.

## Decision

The current configuration uses:

restart: no

This prevents Jellyfin from starting before storage dependencies are
confirmed.

The current startup sequence is:

1.  Operating system available.
2.  Network available.
3.  NFS mounts available.
4.  Jellyfin started through controlled process.

## Reason

The priority is service correctness and data availability over automatic
restart.

Starting a media service without access to its library can create
inconsistent behaviour, failed scans, and unnecessary recovery actions.

## Future Improvement

The long-term solution should provide dependency-aware startup.

Possible implementations:

-   systemd dependency chain:
    -   network-online.target
    -   NFS mount availability
    -   docker.service
    -   Jellyfin startup
-   CHOMS Controller orchestration:
    -   validate infrastructure health
    -   verify storage availability
    -   start application services

## Status

Accepted.

The current configuration is intentional and documented.
