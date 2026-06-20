#!/bin/bash
set -e

apt update
apt install exfatprogs -y

mkdir -p /media/ssd-media

if ! grep -q "1CBB-DB78" /etc/fstab; then
  echo "UUID=1CBB-DB78 /media/ssd-media exfat defaults,nofail,uid=1000,gid=1000,umask=0022 0 0" >> /etc/fstab
fi

systemctl daemon-reload
mount -a
findmnt /media/ssd-media
