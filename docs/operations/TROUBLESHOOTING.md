# CHOMS Troubleshooting

## qBittorrent Mount Issue

If qBittorrent shows `/downloads` mounted on `/dev/sda2`, it is using the NAS system SSD incorrectly.

Correct state:

    /downloads -> /dev/md0
    /config    -> /dev/md0
    /logs      -> /dev/md0
    /movies    -> /dev/md1
    /series    -> /dev/md1

Check:

    docker exec qbittorrent df -h /downloads /config /logs /movies /series
