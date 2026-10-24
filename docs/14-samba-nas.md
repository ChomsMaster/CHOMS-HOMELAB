# Samba NAS

CHOMS-HOMELAB provides SMB/CIFS file sharing through Samba.

## Shares

| Share | Path | Purpose |
|---|---|---|
| Storage | /data/storage | Main NAS storage |
| Media | /media/ssd-media | External SSD media library |

## Access

Windows:

\\192.168.1.138\Storage
\\192.168.1.138\Media

User:

chomsmaster

## Validation

sudo testparm
sudo systemctl status smbd
smbclient -L localhost -U chomsmaster
