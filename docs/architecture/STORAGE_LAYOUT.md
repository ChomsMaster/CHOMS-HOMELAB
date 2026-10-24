# CHOMS Storage Layout

## NAS

System SSD:

    120 GB

Storage RAID:

    /srv/storage
    RAID0 2 x 3 TB
    Approx usable: 5.5 TB

Media RAID:

    /srv/media
    RAID0 2 x 2 TB
    Approx usable: 3.6 TB

## Important Warning

Current NAS arrays are RAID0.

RAID0 provides capacity and speed but no disk redundancy.

Backups are mandatory for important data.

## Generic media output

Library paths remain `/srv/media/Movies` and `/srv/media/Series`.
Application-specific configuration is outside the public scope.
