#!/bin/sh
# Finish setting up a freshly-configured Raspberry Pi, run ON THE PI:
#
#   sudo WIFI_SSID='...' WIFI_PSK='...' sh finish-rpi-setup.sh
#
# Fixes the two things a card-level configuration cannot: the rfkill soft-block
# on the radio, and joining a specific band.
#
# The soft-block is the subtle one. Setting the regulatory country in
# /etc/modprobe.d and /etc/default/crda works — `iw reg get` reports FR — but
# Raspberry Pi OS *separately* soft-blocks the radio on first boot and only
# clears that when the country is set through its own tooling. So the country
# is right, and the radio is still off. `rfkill unblock` is what actually turns
# it on, and systemd-rfkill persists that across reboots.
set -eu

SSID="${WIFI_SSID:?set WIFI_SSID}"
PSK="${WIFI_PSK:?set WIFI_PSK}"
NEW_HOSTNAME="${NEW_HOSTNAME:-raspi}"
COUNTRY="${COUNTRY:-FR}"

say() { printf '  %s\n' "$*"; }
hdr() { printf '\n== %s ==\n' "$*"; }
[ "$(id -u)" -eq 0 ] || { echo "Run with sudo." >&2; exit 1; }

hdr "Radio"
if raspi-config nonint do_wifi_country "$COUNTRY" 2>/dev/null; then
  say "country set via raspi-config (which also clears its own soft-block)"
else
  say "raspi-config unavailable; relying on rfkill below"
fi
rfkill unblock wifi
rfkill unblock all 2>/dev/null || true
sleep 2
rfkill list wifi | sed 's/^/  /'
ip link set wlan0 up 2>/dev/null || true
sleep 3
say "wlan0 is now: $(nmcli -t -f DEVICE,STATE dev status | sed -n 's/^wlan0://p')"

hdr "Joining $SSID"
nmcli dev wifi rescan 2>/dev/null || true
sleep 6
if ! nmcli -t -f SSID dev wifi list | grep -Fxq "$SSID"; then
  say "WARNING: '$SSID' not visible in the scan. Visible networks:"
  nmcli -t -f SSID,FREQ,SIGNAL dev wifi list | head -10 | sed 's/^/    /'
fi
# Replace rather than edit: re-running this must not stack duplicate profiles.
nmcli con delete "$SSID" >/dev/null 2>&1 || true
nmcli con add type wifi con-name "$SSID" ifname wlan0 ssid "$SSID" \
  wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$PSK" \
  connection.autoconnect yes connection.autoconnect-priority 20 >/dev/null
say "profile created (priority 20)"

# Any other wifi profile drops below it, so the chosen band wins when both are
# in range rather than whichever NetworkManager happened to see first.
for c in $(nmcli -t -f NAME,TYPE con show | sed -n 's/:802-11-wireless$//p'); do
  [ "$c" = "$SSID" ] && continue
  nmcli con mod "$c" connection.autoconnect-priority 5 2>/dev/null \
    && say "lowered priority of '$c' to 5"
done

nmcli con up "$SSID" 2>&1 | tail -1 | sed 's/^/  /' || say "activation did not report success; state below"

hdr "Hostname"
CURRENT=$(hostname)
if [ "$CURRENT" != "$NEW_HOSTNAME" ]; then
  hostnamectl set-hostname "$NEW_HOSTNAME"
  # /etc/hosts must follow, or sudo warns about resolving the host on every call.
  sed -i "s/127\.0\.1\.1.*/127.0.1.1\t$NEW_HOSTNAME/" /etc/hosts
  grep -q "127.0.1.1" /etc/hosts || printf '127.0.1.1\t%s\n' "$NEW_HOSTNAME" >> /etc/hosts
  say "renamed '$CURRENT' -> '$NEW_HOSTNAME' (mDNS becomes $NEW_HOSTNAME.local)"
else
  say "already '$NEW_HOSTNAME'"
fi

hdr "Result"
sleep 5
nmcli -t -f DEVICE,TYPE,STATE,CONNECTION dev status | grep -E "wlan0|eth0" | sed 's/^/  /'
say "wlan0 address: $(ip -4 -br addr show wlan0 | awk '{print $3}')"
say "If that shows a 192.168.1.x address, wifi is up. The .99 reservation"
say "applies to whichever interface MAC you registered on the Freebox —"
say "wlan0 has a different MAC to eth0, so check that if the address is unexpected."
