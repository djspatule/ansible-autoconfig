#!/bin/sh
# Configure an ALREADY-FLASHED Raspberry Pi OS card for a headless first boot:
# SSH on, a named user with your key, wifi with a regulatory country.
#
#   sudo WIFI_SSID='...' WIFI_PSK='...' sh scripts/helpers/configure-rpi-card.sh --check
#   sudo WIFI_SSID='...' WIFI_PSK='...' sh scripts/helpers/configure-rpi-card.sh
#
# Why not custom.toml: that file is applied by a firstboot hook which Raspberry
# Pi Imager adds to cmdline.txt when IT writes the card. `rpi-imager --cli` does
# no customisation, so the hook is absent, and a custom.toml sitting on the boot
# partition is read by nothing and silently ignored. That is exactly what
# happened on the first attempt — the card booted stock, kept the hostname
# "raspberrypi", never joined wifi and never enabled SSH.
#
# Everything below instead uses mechanisms that are present and ENABLED on the
# stock image, each verified by reading the image's own scripts:
#   * sshswitch.service  -> reads <boot>/ssh            (enabled in multi-user.target.wants)
#   * userconfig.service -> reads <boot>/userconf.txt   (username:password_hash)
#   * NetworkManager     -> reads /etc/NetworkManager/system-connections/*.nmconnection
set -eu

ROOTFS="${ROOTFS:-/run/media/${SUDO_USER:-lion}/rootfs}"
BOOTFS="${BOOTFS:-/run/media/${SUDO_USER:-lion}/bootfs}"
PI_USER="${PI_USER:-lion}"
COUNTRY="${COUNTRY:-FR}"
PUBKEY_FILE="${PUBKEY_FILE:-/home/${SUDO_USER:-lion}/.ssh/id_ed25519_homelab.pub}"

say() { printf '  %s\n' "$*"; }
hdr() { printf '\n== %s ==\n' "$*"; }

[ "$(id -u)" -eq 0 ] || { echo "Must run as root: sudo sh $0" >&2; exit 1; }
CHECK_ONLY=0; [ "${1:-}" = "--check" ] && CHECK_ONLY=1

hdr "Target"
[ -d "$ROOTFS/etc" ] || { echo "ERROR: $ROOTFS is not a rootfs." >&2; exit 1; }
[ -d "$BOOTFS" ]     || { echo "ERROR: $BOOTFS not found." >&2; exit 1; }
# Never operate on the running machine.
[ "$(stat -c %d /)" != "$(stat -c %d "$ROOTFS")" ] \
  || { echo "ERROR: $ROOTFS is on the same filesystem as / — that is this laptop." >&2; exit 1; }
say "rootfs: $ROOTFS"
say "bootfs: $BOOTFS"
say "stock user on image: $(awk -F: '$3==1000 {print $1}' "$ROOTFS/etc/passwd")"

: "${WIFI_SSID:?set WIFI_SSID in the environment}"
: "${WIFI_PSK:?set WIFI_PSK in the environment}"
[ -r "$PUBKEY_FILE" ] || { echo "ERROR: no readable public key at $PUBKEY_FILE" >&2; exit 1; }

hdr "Plan"
say "user:    $PI_USER  (renamed from the stock uid-1000 user by userconfig.service)"
say "ssh:     enabled via <boot>/ssh, key authorised from $(basename "$PUBKEY_FILE")"
say "wifi:    $WIFI_SSID, country $COUNTRY"
say "cleanup: remove the inert custom.toml left by the previous attempt"
[ "$CHECK_ONLY" -eq 1 ] && { printf '\n--check: nothing written.\n'; exit 0; }

STOCK_USER=$(awk -F: '$3==1000 {print $1}' "$ROOTFS/etc/passwd")
STOCK_HOME=$(awk -F: '$3==1000 {print $6}' "$ROOTFS/etc/passwd")

hdr "SSH"
: > "$BOOTFS/ssh"
say "created <boot>/ssh — sshswitch.service enables sshd on first boot"

# Placed in the STOCK user's home: userconf renames that account with
# `usermod -m`, which moves the home directory and carries this with it.
install -d -m 700 -o 1000 -g 1000 "$ROOTFS$STOCK_HOME/.ssh"
cat "$PUBKEY_FILE" > "$ROOTFS$STOCK_HOME/.ssh/authorized_keys"
chmod 600 "$ROOTFS$STOCK_HOME/.ssh/authorized_keys"
chown 1000:1000 "$ROOTFS$STOCK_HOME/.ssh/authorized_keys"
say "authorised your key in $STOCK_HOME/.ssh (follows the rename to $PI_USER)"

hdr "User"
# A password is still set: if the key somehow does not take, a console login is
# the only way back into a headless box without re-flashing.
CONSOLE_PW=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 20)
PW_HASH=$(printf '%s' "$CONSOLE_PW" | openssl passwd -6 -stdin)
printf '%s:%s\n' "$PI_USER" "$PW_HASH" > "$BOOTFS/userconf.txt"
chmod 600 "$BOOTFS/userconf.txt"
say "wrote <boot>/userconf.txt — renames '$STOCK_USER' to '$PI_USER'"

hdr "Wifi"
NM_DIR="$ROOTFS/etc/NetworkManager/system-connections"
install -d -m 755 "$NM_DIR"
PSK_HASH=$(wpa_passphrase "$WIFI_SSID" "$WIFI_PSK" | sed -n 's/^[[:space:]]*psk=\(.*\)$/\1/p' | head -1)
[ -n "$PSK_HASH" ] || { echo "ERROR: wpa_passphrase produced no PSK" >&2; exit 1; }
UUID=$(cat /proc/sys/kernel/random/uuid)
cat > "$NM_DIR/$WIFI_SSID.nmconnection" <<NMCONN
[connection]
id=$WIFI_SSID
uuid=$UUID
type=wifi
autoconnect=true

[wifi]
mode=infrastructure
ssid=$WIFI_SSID

[wifi-security]
key-mgmt=wpa-psk
psk=$PSK_HASH

[ipv4]
method=auto

[ipv6]
method=auto
NMCONN
# NetworkManager refuses to load a profile that is not 0600 root-owned.
chmod 600 "$NM_DIR/$WIFI_SSID.nmconnection"
chown 0:0 "$NM_DIR/$WIFI_SSID.nmconnection"
say "wrote NetworkManager profile for '$WIFI_SSID' (PSK hashed, 0600 root)"

# Without a regulatory country the radio stays rfkill-blocked and the Pi never
# appears on the network at all.
install -d -m 755 "$ROOTFS/etc/modprobe.d" "$ROOTFS/etc/default"
printf 'options cfg80211 ieee80211_regdom=%s\n' "$COUNTRY" > "$ROOTFS/etc/modprobe.d/cfg80211.conf"
printf 'REGDOMAIN=%s\n' "$COUNTRY" > "$ROOTFS/etc/default/crda"
say "set WLAN country to $COUNTRY"

hdr "Cleanup"
if [ -e "$BOOTFS/custom.toml" ]; then
  rm -f "$BOOTFS/custom.toml"
  say "removed the inert custom.toml (nothing on this image reads it)"
fi

sync
hdr "Done"
say "Console password for $PI_USER (physical access only; SSH uses your key):"
printf '\n      %s\n\n' "$CONSOLE_PW"
say "Eject:  udisksctl unmount -b ${BOOTFS##*/} ; see lsblk for the device"
say "Then boot the Pi on ethernet and try:  ssh $PI_USER@raspberrypi.local"
say "Hostname stays 'raspberrypi' — nothing here renames it, by design."
