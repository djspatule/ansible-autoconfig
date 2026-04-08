#!/bin/sh
set -eu

repo_url="${AUTOCONFIG_REPO_URL:-https://github.com/djspatule/ansible-autoconfig.git}"
branch="${AUTOCONFIG_BRANCH:-server-bootstrap}"
repo_dir="${AUTOCONFIG_REPO_DIR:-/opt/ansible-pull}"
playbook="${1:-${AUTOCONFIG_PLAYBOOK:-server_core.yml}}"
vault_password_file="${AUTOCONFIG_VAULT_PASSWORD_FILE:-}"

if [ "$(id -u)" -ne 0 ]; then
  printf '%s\n' 'Run this bootstrap script as root.' >&2
  exit 1
fi

if [ ! -r /etc/os-release ]; then
  printf '%s\n' 'Cannot detect the operating system.' >&2
  exit 1
fi

. /etc/os-release

# Install only the minimum needed to let the repo configure the rest. That
# keeps first-boot logic small and leaves long-term state in Ansible itself.
case "${ID}:${ID_LIKE:-}" in
  ubuntu:*|debian:*|linuxmint:*|pop:*|*:*debian*)
    apt-get update
    apt-get install -y git ansible-core
    ;;
  arch:*|manjaro:*|endeavouros:*|*:*arch*)
    pacman -Syu --noconfirm git ansible-core
    ;;
  *)
    printf 'Unsupported distribution: %s\n' "$ID" >&2
    exit 1
    ;;
esac

# Clone or fast-forward the repo before the first pull so the same script works
# on both a blank machine and a previously bootstrapped one.
if [ ! -d "$repo_dir/.git" ]; then
  git clone --branch "$branch" "$repo_url" "$repo_dir"
else
  git -C "$repo_dir" fetch --prune origin
  git -C "$repo_dir" checkout "$branch"
  git -C "$repo_dir" pull --ff-only origin "$branch"
fi

if [ -f "$repo_dir/requirements.yml" ]; then
  ansible-galaxy collection install -r "$repo_dir/requirements.yml"
fi

set -- ansible-pull -U "$repo_url" -C "$branch" -d "$repo_dir"

if [ -n "$vault_password_file" ]; then
  set -- "$@" --vault-password-file "$vault_password_file"
fi

set -- "$@" "$playbook"
exec "$@"
