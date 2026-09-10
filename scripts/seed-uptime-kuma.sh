#!/bin/sh
# Run the Uptime Kuma seeder from serverannah, against the container directly.
#
# Why not just point the Python script at https://status.dinnizer.com: that route
# is behind Caddy basic auth, so the socket.io handshake would have to carry a
# second set of credentials, and the Kuma admin password would travel over the
# public internet to reach a service sitting on the same machine. Going through
# the shared Docker network avoids both.
#
# Usage (on serverannah):
#   sudo sh scripts/seed-uptime-kuma.sh --dry-run
#   sudo sh scripts/seed-uptime-kuma.sh
set -eu

repo_dir="${AUTOCONFIG_REPO_DIR:-/opt/ansible-pull}"
network="${KUMA_NETWORK:-autoconfig-services}"
target="${KUMA_URL:-http://uptime-kuma:3001}"

# Mounted read-only: the seeder only ever reads host_vars and the secrets.
exec docker run --rm -i \
  --network "$network" \
  -v "$repo_dir:/repo:ro" \
  -v /etc/ansible/secrets:/etc/ansible/secrets:ro \
  -e "KUMA_USERNAME=${KUMA_USERNAME:-}" \
  -e "KUMA_PASSWORD=${KUMA_PASSWORD:-}" \
  -w /repo \
  python:3.12-slim \
  sh -c "pip install --quiet uptime-kuma-api pyyaml && python scripts/seed-uptime-kuma.py --url '$target' $*"
