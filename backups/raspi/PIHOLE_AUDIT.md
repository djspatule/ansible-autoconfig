# Raspi Pi-hole Audit

## Status

This audit is now good enough to automate the current Pi-hole behavior.

Readable sources used:

- `/etc/pihole/pihole.toml`
- `/etc/pihole-updatelists.conf`
- copied raspi backup under `backups/raspi/etc/pihole-bak/pihole/`
- `gravity.db` extracted from that backup

The copied backup let us read the files and databases that were previously not
readable through the live sshfs mount.

## Visible Live Settings

Source: `/etc/pihole/pihole.toml`

- upstreams:
  - `8.8.8.8`
  - `8.8.4.4`
  - `2001:4860:4860::8888`
  - `2001:4860:4860::8844`
- local domain: `lan`
- listening mode: `LOCAL`
- interface: `eth0`
- query logging: enabled
- DNSSEC: disabled
- `domainNeeded = true`
- `expandHosts = true`
- `bogusPriv = true`
- `EDNS0ECS = true`
- `piholePTR = "PI.HOLE"`
- port: `53`
- reverse servers: empty

Source: `/etc/pihole-updatelists.conf`

- no remote adlist/whitelist/blacklist URLs are configured there

Source: `gravity.db`

- enabled adlists: `28`
- enabled exact allowlist entries: `197`
- domainlist types present: only `type = 0`

Interpretation:

- there is a substantial exact allowlist
- there is no evidence in the readable DB of active blacklist or regex policy

Source: copied backup files

- `/etc/pihole/adlists.list` contains only the legacy StevenBlack line and is
  not the real source of truth anymore
- `/etc/pihole/local.list` is only the Pi-hole placeholder text
- `/etc/pihole/hosts/custom.list` contains no custom entries
- `/etc/pihole-updatelists.conf` has no remote list URLs configured

## Cutover Assessment

Safe conclusions:

- `serverannah` Pi-hole should default to Google upstreams, `LOCAL` listening,
  and `lan` domain to match the visible raspi settings.
- The update-lists helper is not currently pulling any remote list sources.
- The current live policy appears to be driven primarily by:
  - Pi-hole core config in `pihole.toml`
  - enabled adlists stored in `gravity.db`
  - exact allowlist entries stored in `gravity.db`

Remaining caution:

- we have not yet encoded the `gravity.db` adlist/allowlist import into the
  Ansible Pi-hole task itself
- that is now an implementation gap, not an information gap

## Recommendation

Do **not** cut over the household DNS from raspi to `serverannah` until the
Ansible Pi-hole role can import at least these three things:

1. the `pihole.toml` behavior already aligned in the role
2. the `28` enabled adlists from `gravity.db`
3. the `197` exact allowlist entries from `gravity.db`

At this point, the blocker is no longer discovery. The blocker is implementing
that import path in the Ansible Pi-hole role and validating it on a non-critical
host or maintenance window.
