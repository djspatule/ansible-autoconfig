#!/bin/sh
# Prepare a flashed Raspberry Pi OS image so it joins wifi and is reachable by
# SSH on first boot. Run it against the MOUNTED image, as root, from the machine
# that flashed the drive:
#
#   sudo sh scripts/helpers/fix-rpi-image-wifi.sh --check    # report only, change nothing
#   sudo sh scripts/helpers/fix-rpi-image-wifi.sh
#
# Why this is needed at all: Raspberry Pi OS keeps the wifi radio soft-blocked
# by rfkill until a WLAN regulatory country is configured. With no country the
# radio never comes up, so the Pi never associates, never requests a DHCP lease
# and never answers SSH — it simply vanishes. It bites 5 GHz hardest, which is
# the band this network's profile uses.
#
# The script is idempotent: run it twice and the second run reports "already
# set" for everything.
set -eu

ROOTFS="${ROOTFS:-/run/media/$(logname 2>/dev/null || echo "$SUDO_USER")/rootfs}"
BOOTFS="${BOOTFS:-/run/media/$(logname 2>/dev/null || echo "$SUDO_USER")/bootfs}"
COUNTRY="${COUNTRY:-FR}"
# The 5 GHz profile the image already has, and the 2.4 GHz twin to add as a
# fallback. 2.4 GHz travels through walls far better, which matters for a Pi
# that has no screen to tell you why it did not connect.
SSID_5="${SSID_5:-#M+L_5}"
SSID_24="${SSID_24:-#M+L}"

CHECK_ONLY=0
[ "${1:-}" = "--check" ] && CHECK_ONLY=1

say()  { printf '  %s\n' "$*"; }
head_() { printf '\n== %s ==\n' "$*"; }

if [ "$(id -u)" -ne 0 ]; then
  echo "This must run as root (it writes to root-owned files on the image): sudo sh $0" >&2
  exit 1
fi

head_ "Target"
say "rootfs: $ROOTFS"
say "bootfs: $BOOTFS"
[ -d "$ROOTFS/etc" ] || { echo "ERROR: $ROOTFS does not look like a Linux rootfs (no /etc)." >&2; exit 1; }
[ -d "$BOOTFS" ]     || { echo "ERROR: $BOOTFS not found." >&2; exit 1; }
if [ ! -f "$ROOTFS/etc/rpi-issue" ] && [ ! -d "$ROOTFS/boot/firmware" ]; then
  say "WARNING: this does not obviously look like a Raspberry Pi OS image. Continuing anyway."
fi
# Refuse to operate on the running system by mistake.
if [ "$(stat -c %d /)" = "$(stat -c %d "$ROOTFS")" ]; then
  echo "ERROR: $ROOTFS is on the same filesystem as / — that is this machine, not the image." >&2
  exit 1
fi

NM_DIR="$ROOTFS/etc/NetworkManager/system-connections"

head_ "Current state"
say "SSH enabled on image: $([ -e "$ROOTFS/etc/systemd/system/multi-user.target.wants/ssh.service" ] && echo yes || echo NO)"
say "users (uid>=1000):    $(awk -F: '$3>=1000 && $3<65534 {printf "%s ", $1}' "$ROOTFS/etc/passwd" 2>/dev/null)"
# find, not ls: these SSIDs contain '#' and '+', which ls output does not
# survive cleanly.
say "wifi profiles:        $(find "$NM_DIR" -maxdepth 1 -name '*.nmconnection' -printf '%f ' 2>/dev/null)"
if grep -rqsiE '^[[:space:]]*(country|REGDOMAIN)=' "$ROOTFS/etc/default/crda" \
     "$ROOTFS/etc/wpa_supplicant/wpa_supplicant.conf" "$ROOTFS/etc/modprobe.d" 2>/dev/null; then
  say "wifi country:         already set"
else
  say "wifi country:         NOT SET  <-- this is why the radio stays blocked"
fi

if [ "$CHECK_ONLY" -eq 1 ]; then
  printf '\n--check: nothing was modified.\n'
  exit 0
fi

head_ "Setting the WLAN regulatory country to $COUNTRY"
# Belt and braces, because which one the image honours depends on whether
# wireless-regdb/crda is installed and whether wpa_supplicant or NetworkManager
# owns the radio. All three are harmless when redundant.
mkdir -p "$ROOTFS/etc/modprobe.d" "$ROOTFS/etc/default" "$ROOTFS/etc/wpa_supplicant"

printf 'options cfg80211 ieee80211_regdom=%s\n' "$COUNTRY" \
  > "$ROOTFS/etc/modprobe.d/cfg80211.conf"
say "wrote /etc/modprobe.d/cfg80211.conf (kernel-level, applies at boot)"

printf 'REGDOMAIN=%s\n' "$COUNTRY" > "$ROOTFS/etc/default/crda"
say "wrote /etc/default/crda"

WPA="$ROOTFS/etc/wpa_supplicant/wpa_supplicant.conf"
if [ -f "$WPA" ] && grep -qsE '^[[:space:]]*country=' "$WPA"; then
  sed -i "s/^[[:space:]]*country=.*/country=$COUNTRY/" "$WPA"
  say "updated country= in wpa_supplicant.conf"
else
  printf 'country=%s\n' "$COUNTRY" >> "$WPA"
  chmod 600 "$WPA"
  say "added country= to wpa_supplicant.conf"
fi

# A persisted soft-block from a previous boot survives on the image and would
# keep the radio down even once the country is set.
if ls "$ROOTFS/var/lib/systemd/rfkill/"*wlan* >/dev/null 2>&1; then
  rm -f "$ROOTFS/var/lib/systemd/rfkill/"*wlan*
  say "cleared a persisted wlan rfkill soft-block"
fi

head_ "Wifi profiles"
SRC="$NM_DIR/$SSID_5.nmconnection"
if [ ! -f "$SRC" ]; then
  say "no profile for '$SSID_5' — cannot derive the 2.4 GHz fallback."
  say "Create one on the Pi later, or re-flash with wifi set in Raspberry Pi Imager."
else
  if grep -qsE '^[[:space:]]*psk=' "$SRC"; then
    say "'$SSID_5' profile contains a PSK: good"
  else
    say "WARNING: '$SSID_5' has NO psk= line — it will not authenticate."
    say "Fix it in Raspberry Pi Imager or add the password on the Pi directly."
  fi
  # Make sure it actually comes up by itself.
  if grep -qsE '^[[:space:]]*autoconnect=false' "$SRC"; then
    sed -i 's/^[[:space:]]*autoconnect=false/autoconnect=true/' "$SRC"
    say "'$SSID_5' had autoconnect=false — enabled it"
  fi

  DST="$NM_DIR/$SSID_24.nmconnection"
  if [ -f "$DST" ]; then
    say "'$SSID_24' fallback profile already present"
  else
    # Same credentials, different SSID, lower autoconnect priority so 5 GHz is
    # still preferred when both are in range.
    sed -e "s/^ssid=.*/ssid=$SSID_24/" \
        -e "s/^id=.*/id=$SSID_24/" \
        -e "/^uuid=/d" \
        "$SRC" > "$DST"
    # A duplicate uuid would make NetworkManager ignore one of the two profiles.
    NEWUUID=$(cat /proc/sys/kernel/random/uuid)
    sed -i "/^\[connection\]/a uuid=$NEWUUID" "$DST"
    grep -qsE '^autoconnect-priority=' "$DST" || sed -i "/^\[connection\]/a autoconnect-priority=-10" "$DST"
    chmod 600 "$DST"
    chown root:root "$DST"
    say "created 2.4 GHz fallback profile '$SSID_24' (lower priority than 5 GHz)"
  fi
fi

head_ "Making sure SSH is on"
if [ -e "$ROOTFS/etc/systemd/system/multi-user.target.wants/ssh.service" ]; then
  say "ssh.service already enabled"
else
  ln -sf /lib/systemd/system/ssh.service \
     "$ROOTFS/etc/systemd/system/multi-user.target.wants/ssh.service"
  say "enabled ssh.service"
fi
# The empty 'ssh' file on the boot partition is the belt to that braces: Pi OS
# enables SSH on first boot if it finds one.
[ -e "$BOOTFS/ssh" ] || { : > "$BOOTFS/ssh"; say "created /boot/ssh"; }

head_ "Done"
say "Unmount cleanly before removing the drive:"
say "  udisksctl unmount -b /dev/sda1 && udisksctl unmount -b /dev/sda2"
say "Then boot the Pi and try:  ssh raspi   (192.168.1.99)"
say "If it still does not appear, the PSK in the profile is the next suspect —"
say "attach a screen and keyboard, or re-flash setting wifi in Raspberry Pi Imager."
