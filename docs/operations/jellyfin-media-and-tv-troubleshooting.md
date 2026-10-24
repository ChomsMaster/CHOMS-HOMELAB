# Jellyfin Media and TV Troubleshooting

## Current media sources

Recommended Jellyfin Movies library sources during transition:

```text
/media/ssd-media/Movies
/mnt/choms-media/Movies
```

Long-term target: move persistent media to the NAS and keep nodes focused on execution.

## Current NAS path

NAS media is mounted on node-01 at:

```text
/mnt/choms-media
```

Movies:

```text
/mnt/choms-media/Movies
```

## TV playback issue

Symptoms:

- TV was kicked out / showed connection issue.
- Computer playback was stable.
- Jellyfin server did not crash.
- LAN tests are healthy.
- TV directly connected to router seemed stable.
- TV reconnected to switch later seemed stable.
- RJ45 connector at TV has broken locking tab.

Most likely causes:

1. TV Ethernet cable/connector micro-disconnects.
2. TV app / DLNA session fragility.
3. Jellyfin DLNA behavior.
4. Switch fault is low probability after iperf3 validation.

## Recommended actions

1. Replace the TV Ethernet cable with one with an intact RJ45 locking tab.
2. Use the official Jellyfin app/client where possible.
3. Avoid Jellyfin DLNA if it keeps causing problems.
4. If using a separate DLNA server, identify it:

```bash
systemctl list-units --type=service | grep -Ei 'dlna|minidlna|readymedia|gerbera'
dpkg -l | grep -Ei 'minidlna|readymedia|gerbera'
```

5. Add NAS movie path to the external DLNA server once identified.
