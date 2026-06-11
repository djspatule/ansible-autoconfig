#!/bin/bash

set -euo pipefail

mountpoint="$HOME/mnt/freebox"
remote=':smb,host=192.168.1.254,user=guest:/Disque dur'

mkdir -p "$mountpoint"

while ! ping -c 1 192.168.1.254 >/dev/null 2>&1; do
  sleep 1
done

if mountpoint -q "$mountpoint"; then
  echo "Already mounted: $mountpoint"
  exit 0
fi

exec rclone mount "$remote" "$mountpoint" \
  --dir-cache-time 10m \
  --vfs-cache-mode full \
  --network-mode
