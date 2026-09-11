#!/bin/sh
# Recover a host locked out by ufw, by editing its filesystem offline.
#
#   sudo sh scripts/helpers/unlock-ufw-on-card.sh --check
#   sudo sh scripts/helpers/unlock-ufw-on-card.sh
#
# Disables ufw at the config level so the machine boots reachable. It does NOT
# hand-edit user.rules: that file has its own format and is rewritten by ufw
# anyway, so flipping ENABLED is both simpler and less likely to corrupt state.
#
# Re-enabling is deliberately left to Ansible. The firewall role allows SSH
# before it enables the deny policy, so the next run restores the firewall
# correctly and with the SSH rule present — which is the failure this recovers
# from in the first place.
set -eu

ROOTFS="${ROOTFS:-/run/media/${SUDO_USER:-lion}/rootfs}"
say() { printf '  %s\n' "$*"; }

[ "$(id -u)" -eq 0 ] || { echo "Must run as root: sudo sh $0" >&2; exit 1; }
[ -d "$ROOTFS/etc" ] || { echo "ERROR: $ROOTFS is not a rootfs." >&2; exit 1; }
# Never touch the running machine.
[ "$(stat -c %d /)" != "$(stat -c %d "$ROOTFS")" ] \
  || { echo "ERROR: $ROOTFS is on the same filesystem as / — that is this laptop." >&2; exit 1; }

CONF="$ROOTFS/etc/ufw/ufw.conf"
[ -f "$CONF" ] || { echo "ERROR: no $CONF — is ufw even installed there?" >&2; exit 1; }

printf '\n== Current state ==\n'
say "rootfs:      $ROOTFS"
say "ufw.conf:    $(grep -E '^ENABLED=' "$CONF" || echo 'no ENABLED line')"
say "rules for 22: $(grep -c '22' "$ROOTFS/etc/ufw/user.rules" 2>/dev/null || echo 0)"

if [ "${1:-}" = "--check" ]; then
  printf '\n--check: nothing written.\n'
  exit 0
fi

printf '\n== Disabling ufw ==\n'
cp -a "$CONF" "$CONF.bak-$(date +%Y%m%d-%H%M%S)"
sed -i 's/^ENABLED=.*/ENABLED=no/' "$CONF"
say "set ENABLED=no (original kept alongside as .bak-<timestamp>)"

# systemd starts ufw independently of ufw.conf, so the flag alone is not enough.
if [ -e "$ROOTFS/etc/systemd/system/multi-user.target.wants/ufw.service" ]; then
  rm -f "$ROOTFS/etc/systemd/system/multi-user.target.wants/ufw.service"
  say "disabled ufw.service at boot"
fi

sync
printf '\n== Done ==\n'
say "Boot the Pi; SSH will answer again."
say "Then run ansible-pull — the firewall role now allows SSH BEFORE enabling"
say "the deny policy, so it re-arms the firewall without locking you out."
