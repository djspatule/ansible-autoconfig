#!/bin/bash

set -euo pipefail

mountpoint="$HOME/mnt/serverannah"
remote="serverannah:/mnt/"

mkdir -p "$mountpoint"

while ! ssh -o BatchMode=yes -o ConnectTimeout=5 serverannah true >/dev/null 2>&1; do
  sleep 1
done

if mountpoint -q "$mountpoint"; then
  echo "Already mounted: $mountpoint"
  exit 0
fi

exec sshfs "$remote" "$mountpoint" \
  -o reconnect \
  -o ServerAliveInterval=15 \
  -o ServerAliveCountMax=3 \
  -o follow_symlinks \
  -o idmap=user
