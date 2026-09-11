#!/bin/sh
# Flash Raspberry Pi OS to a removable device and configure it for a headless
# first boot: wifi, SSH by key, hostname, locale.
#
#   sudo WIFI_SSID='...' WIFI_PSK='...' sh scripts/helpers/flash-rpi.sh --check
#   sudo WIFI_SSID='...' WIFI_PSK='...' sh scripts/helpers/flash-rpi.sh /dev/sdX
#
# THIS DESTROYS EVERYTHING ON THE TARGET DEVICE.
#
# No credentials live in this file — it is committed to a public repository.
# The wifi passphrase is read from the environment and converted to a PSK hash
# before it touches the card, so the plaintext is never written to disk.
#
# Customisation uses custom.toml, the first-boot mechanism Raspberry Pi OS
# (Bookworm and later) reads from the boot partition. That is the same thing the
# Imager GUI writes, which is why this needs no GUI at all.
set -eu

IMAGE_URL="${IMAGE_URL:-https://downloads.raspberrypi.com/raspios_lite_arm64_latest}"
HOSTNAME_="${PI_HOSTNAME:-raspi}"
PI_USER="${PI_USER:-lion}"
COUNTRY="${COUNTRY:-FR}"
KEYMAP="${KEYMAP:-fr}"
TIMEZONE="${TIMEZONE:-Europe/Paris}"
PUBKEY_FILE="${PUBKEY_FILE:-/home/lion/.ssh/id_ed25519_homelab.pub}"

say() { printf '  %s\n' "$*"; }
hdr() { printf '\n== %s ==\n' "$*"; }

[ "$(id -u)" -eq 0 ] || { echo "Must run as root: sudo sh $0 ..." >&2; exit 1; }

CHECK_ONLY=0
case "${1:-}" in --check) CHECK_ONLY=1; TARGET="${2:-/dev/sda}" ;; *) TARGET="${1:-}" ;; esac
[ -n "$TARGET" ] || { echo "Usage: sudo sh $0 [--check] /dev/sdX" >&2; exit 1; }

hdr "Target safety checks"
[ -b "$TARGET" ] || { echo "ERROR: $TARGET is not a block device." >&2; exit 1; }
BASE=$(basename "$TARGET")
# Refuse anything that is not removable. An internal NVMe would be silent, total
# and unrecoverable data loss, so this is a hard stop rather than a prompt.
[ "$(cat "/sys/block/$BASE/removable" 2>/dev/null || echo 0)" = "1" ] \
  || { echo "ERROR: $TARGET is not removable. Refusing." >&2; exit 1; }
# Refuse if any partition of it is currently the source of a system mount.
if lsblk -no MOUNTPOINTS "$TARGET" | grep -qE '^/$|^/boot|^/home'; then
  echo "ERROR: $TARGET carries a system mount. Refusing." >&2; exit 1
fi
say "device:    $TARGET ($(lsblk -dno SIZE "$TARGET" | tr -d ' '), $(lsblk -dno TRAN "$TARGET"), removable)"
say "model:     $(lsblk -dno MODEL "$TARGET")"
say "it holds:  $(lsblk -no LABEL "$TARGET" | tr '\n' ' ')"

hdr "Configuration that will be applied"
: "${WIFI_SSID:?set WIFI_SSID in the environment}"
: "${WIFI_PSK:?set WIFI_PSK in the environment}"
[ -r "$PUBKEY_FILE" ] || { echo "ERROR: no readable public key at $PUBKEY_FILE" >&2; exit 1; }
say "hostname:  $HOSTNAME_"
say "user:      $PI_USER  (SSH by key only; password login disabled)"
say "ssh key:   $(cut -c1-40 "$PUBKEY_FILE")..."
say "wifi:      $WIFI_SSID  (country $COUNTRY)"
say "image:     $IMAGE_URL"

if [ "$CHECK_ONLY" -eq 1 ]; then
  printf '\n--check: nothing written. Re-run without --check to flash.\n'
  exit 0
fi

hdr "Unmounting any existing partitions"
for p in $(lsblk -nlo NAME "$TARGET" | tail -n +2); do
  if mountpoint -q "/dev/$p" 2>/dev/null || grep -q "^/dev/$p " /proc/mounts; then
    if umount "/dev/$p" 2>/dev/null; then
      say "unmounted /dev/$p"
    else
      say "could not unmount /dev/$p (udisks is asked below)"
    fi
  fi
done
# udisks automounts, so ask it too rather than fighting it.
for p in $(lsblk -nlo NAME "$TARGET" | tail -n +2); do
  runuser -u "${SUDO_USER:-lion}" -- udisksctl unmount -b "/dev/$p" >/dev/null 2>&1 || true
done

hdr "Writing the image (this takes several minutes)"
rpi-imager --cli "$IMAGE_URL" "$TARGET"
say "image written and verified"

hdr "Applying first-boot customisation"
partprobe "$TARGET" 2>/dev/null || true
sleep 3
BOOTPART="${TARGET}1"
[ -b "$BOOTPART" ] || BOOTPART="${TARGET}p1"
MNT=$(mktemp -d)
mount "$BOOTPART" "$MNT"

# Hash both secrets so no plaintext lands on the card.
PSK_HASH=$(wpa_passphrase "$WIFI_SSID" "$WIFI_PSK" | sed -n 's/^[[:space:]]*psk=\(.*\)$/\1/p' | head -1)
[ -n "$PSK_HASH" ] || { echo "ERROR: wpa_passphrase produced no PSK" >&2; umount "$MNT"; exit 1; }
# A console password still has to exist for physical recovery, but SSH is
# key-only so this is never used over the network. Random, and printed once.
CONSOLE_PW=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 20)
PW_HASH=$(printf '%s' "$CONSOLE_PW" | openssl passwd -6 -stdin)

cat > "$MNT/custom.toml" <<TOML
# Written by scripts/helpers/flash-rpi.sh. Raspberry Pi OS consumes this on first boot.
config_version = 1

[system]
hostname = "$HOSTNAME_"

[user]
name = "$PI_USER"
password = "$PW_HASH"
password_encrypted = true

[ssh]
enabled = true
# Key only. A headless box on a family LAN should not accept password logins.
password_authentication = false
authorized_keys = [ "$(cat "$PUBKEY_FILE")" ]

[wlan]
ssid = "$WIFI_SSID"
password = "$PSK_HASH"
password_encrypted = true
hidden = false
# Without a country the radio stays rfkill-blocked and the Pi never appears.
# This is the setting whose absence broke the previous card.
country = "$COUNTRY"

[locale]
keymap = "$KEYMAP"
timezone = "$TIMEZONE"
TOML
chmod 600 "$MNT/custom.toml"
say "wrote custom.toml (wifi PSK and console password both hashed)"

sync
umount "$MNT"; rmdir "$MNT"

hdr "Done"
say "Console password for $PI_USER (physical access only, SSH is key-based):"
printf '\n      %s\n\n' "$CONSOLE_PW"
say "Save that somewhere now — it is not stored anywhere else."
say "Eject, put the card in the Pi, power on, then:  ssh $PI_USER@$HOSTNAME_"
say "First boot takes a couple of minutes before it joins wifi."
