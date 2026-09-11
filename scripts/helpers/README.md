# helpers

One-off tools. **Nothing in here runs as part of the playbook** — the nightly
`ansible-pull` never touches this directory.

They live apart from `scripts/` on purpose: `scripts/lint.sh` and
`scripts/bootstrap-server.sh` are part of the normal workflow, while these are
things you run by hand, occasionally, and usually once.

| Tool | What it does |
|---|---|
| `seed-uptime-kuma.py` / `.sh` | Creates Uptime Kuma monitors from `server_reverse_proxy_sites`, and wires the ntfy notification to all of them. A seeder, not config management — Uptime Kuma has no REST API for monitors, so this rides an unofficial socket.io library and is deliberately kept out of the nightly run. |
| `flash-rpi.sh` | Writes Raspberry Pi OS to a removable device and configures a headless first boot (wifi, SSH by key, hostname, locale) via `custom.toml`. Destructive; refuses non-removable targets. |
| `fix-rpi-image-wifi.sh` | Repairs an already-flashed Pi image that will not join wifi, usually because no WLAN regulatory country is set. |

Each script explains its own reasoning in its header comments, including what it
deliberately does *not* do.
