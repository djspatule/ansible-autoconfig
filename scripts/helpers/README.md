# helpers

One-off tools. **Nothing in here runs as part of the playbook** — the nightly
`ansible-pull` never touches this directory.

They live apart from `scripts/` on purpose: `scripts/lint.sh` and
`scripts/bootstrap-server.sh` are part of the normal workflow, while these are
things you run by hand, occasionally, and usually once.

| Tool | What it does |
|---|---|
| `seed-uptime-kuma.py` / `.sh` | Creates Uptime Kuma monitors from `server_reverse_proxy_sites`, and wires the ntfy notification to all of them. A seeder, not config management — Uptime Kuma has no REST API for monitors, so this rides an unofficial socket.io library and is deliberately kept out of the nightly run. |
| `flash-rpi.sh` | Writes Raspberry Pi OS to a removable device. Destructive; refuses non-removable targets. Its `custom.toml` step does **not** work — see below — so follow it with `configure-rpi-card.sh`. |
| `configure-rpi-card.sh` | Configures an already-flashed card for headless first boot: SSH on, your key authorised, a named user, wifi with a regulatory country. |
| `finish-rpi-setup.sh` | Run **on the Pi** after first boot: clears the rfkill soft-block, joins a chosen wifi band, sets the hostname. |
| `fix-rpi-image-wifi.sh` | Repairs an already-flashed Pi image that will not join wifi, usually because no WLAN regulatory country is set. |

Each script explains its own reasoning in its header comments, including what it
deliberately does *not* do.

## Why `custom.toml` does not work with `rpi-imager --cli`

`custom.toml` is not read by Raspberry Pi OS on its own. It is applied by a
firstboot hook that Raspberry Pi **Imager** adds to `cmdline.txt` when the GUI
writes the card. `--cli` only writes the image, so that hook is absent and a
`custom.toml` on the boot partition is read by nothing — no error, no log, it is
simply ignored, and the card boots completely stock.

This was diagnosed the hard way: a card written that way kept the default
hostname `raspberrypi`, never joined wifi and never enabled SSH, and the
`custom.toml` was still sitting untouched on the boot partition afterwards.

`configure-rpi-card.sh` uses the mechanisms that are present **and enabled** on
the stock image instead, each verified by reading the image's own scripts:

| Mechanism | Reads | Verified by |
|---|---|---|
| `sshswitch.service` | `<boot>/ssh` | it is symlinked into `multi-user.target.wants` |
| `userconfig.service` | `<boot>/userconf.txt` (`user:hash`) | `userconf-service` line 41 |
| NetworkManager | `/etc/NetworkManager/system-connections/*.nmconnection` | it is the enabled network stack |

## The rfkill trap

Setting the regulatory country on the card works — `iw reg get` on the booted Pi
reports `country FR: DFS-ETSI`. It is still not enough. Raspberry Pi OS
*separately* soft-blocks the radio on first boot and only clears that block when
the country is set through its own tooling:

```
1: phy0: Wireless LAN
        Soft blocked: yes     <- wlan0 stays "unavailable" regardless of country
```

So a card can have a correct country, a valid NetworkManager profile, and still
never join anything. `finish-rpi-setup.sh` runs `rfkill unblock` (and
`raspi-config nonint do_wifi_country`, which clears the block properly);
systemd-rfkill then persists the unblocked state across reboots.
