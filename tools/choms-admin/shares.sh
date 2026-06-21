#!/usr/bin/env bash

set -e

echo "=============================================="
echo " CHOMS-HOMELAB Shared Resources"
echo "=============================================="
echo

printf "%-12s %-8s %-35s\n" "Share" "Status" "Path"
printf "%-12s %-8s %-35s\n" "-----" "------" "----"

testparm -s 2>/dev/null | awk '
/^\[/{
    share=substr($1,2,length($1)-2)
}
/path =/{
    if (share == "printers" || share == "print$") next

    path=$3
    status="OK"

    if(system("[ -d \"" path "\" ]")!=0)
        status="MISSING"

    printf "%-12s %-8s %-35s\n",share,status,path
}
'

echo
echo "=============================================="

echo
echo "Samba Service"

if systemctl is-active --quiet smbd
then
    echo "Status : RUNNING"
else
    echo "Status : STOPPED"
fi

echo

echo "Mounted shares"

mount | grep "/media\|/data" || true
