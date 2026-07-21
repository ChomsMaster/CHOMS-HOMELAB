#!/bin/bash

set -euo pipefail

apt update
apt install samba smbclient -y

mkdir -p /data/storage
chown chomsmaster:chomsmaster /data/storage

cp /etc/samba/smb.conf /etc/samba/smb.conf.bak.$(date +%F-%H%M%S)

python3 - <<'PY'
from pathlib import Path

path = Path("/etc/samba/smb.conf")
text = path.read_text()

shares = r"""

[Storage]
   path = /data/storage
   browseable = yes
   read only = no
   create mask = 0664
   directory mask = 0775
   valid users = chomsmaster

[Media]
   path = /media/ssd-media
   browseable = yes
   read only = no
   create mask = 0664
   directory mask = 0775
   valid users = chomsmaster
"""

for section in ("[Storage]", "[Media]"):
    if section in text:
        print(f"{section} already exists in smb.conf")

if "[Storage]" not in text and "[Media]" not in text:
    path.write_text(text.rstrip() + shares + "\n")
    print("Samba shares added.")
elif "[Storage]" not in text or "[Media]" not in text:
    raise SystemExit("ERROR: Partial Samba share configuration detected. Review /etc/samba/smb.conf manually.")
PY

testparm -s
systemctl restart smbd
systemctl enable smbd

echo "Samba setup completed."
