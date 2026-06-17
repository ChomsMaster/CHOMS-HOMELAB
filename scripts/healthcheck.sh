#!/bin/bash

echo "========================================"
echo "      CHOMS HOMELAB HEALTH CHECK"
echo "========================================"

echo
echo "Hostname:"
hostname

echo
echo "IP Addresses:"
hostname -I

echo
echo "Disk Usage:"
df -h

echo
echo "Memory:"
free -h

echo
echo "Docker Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}"

echo
echo "WireGuard:"
sudo wg

echo
echo "========================================"
echo "Health Check Completed"
echo "========================================"
