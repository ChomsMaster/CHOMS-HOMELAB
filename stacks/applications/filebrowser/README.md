# CHOMS Filebrowser Stack

Role: Web file manager for CHOMS Platform.

## Node

Application Node:

- Host: choms-node-02
- Runtime path: /data/docker/stacks/applications/filebrowser
- Network: choms-backend

## Mounted Paths

- /mnt/choms-storage -> /srv/storage
- /mnt/choms-media -> /srv/media
- /data/projects -> /srv/projects

## Deploy

    choms deploy filebrowser

## Validate

    docker ps --filter "name=choms-filebrowser"
