#!/bin/bash

set -euo pipefail

apt update
apt install minidlna -y

cp /etc/minidlna.conf /etc/minidlna.conf.bak.$(date +%F-%H%M%S)

cat > /etc/minidlna.conf <<'EOFCONF'
network_interface=enp1s0
media_dir=V,/media/ssd-media
friendly_name=CHOMS Media Server
inotify=yes
db_dir=/var/cache/minidlna
log_dir=/var/log
EOFCONF

systemctl enable minidlna
systemctl restart minidlna
minidlnad -R || true
systemctl restart minidlna

echo "MiniDLNA setup completed."
