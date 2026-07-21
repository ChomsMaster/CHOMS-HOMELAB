# Media Server

CHOMS-HOMELAB provides media access using Jellyfin and MiniDLNA.

## Jellyfin

Runs in Docker using host networking for DLNA compatibility.

URL:

http://192.168.1.138:8096

Media paths inside container:

| Host Path | Container Path |
|---|---|
| /data/media | /media |
| /media/ssd-media | /usbmedia |

## MiniDLNA

MiniDLNA provides lightweight DLNA/UPnP access for Smart TVs.

Main path:

/media/ssd-media

Friendly name:

CHOMS Media Server

## Samsung TV

The TV should detect the server under:

Source / Fuente → Connected Devices / Multimedia / Videos

## Validation

docker ps
docker logs jellyfin --tail 50
systemctl status minidlna
