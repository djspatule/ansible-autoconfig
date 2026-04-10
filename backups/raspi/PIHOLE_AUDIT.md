# Raspi Pi-hole Audit

## Status

This audit is now good enough to automate the current Pi-hole behavior.

Readable sources used:

- `/etc/pihole/pihole.toml`
- `/etc/pihole-updatelists.conf`
- copied raspi backup under `backups/raspi/etc/pihole-bak/pihole/`
- `gravity.db` extracted from that backup
- extracted text exports committed under `backups/raspi/etc/pihole/`

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

The information gap is now closed for Pi-hole specifically.

The intended Ansible source-of-truth is:

1. Pi-hole behavior encoded as role vars
2. `backups/raspi/etc/pihole/adlists_enabled.txt`
3. `backups/raspi/etc/pihole/allowlist_exact.txt`
4. `backups/raspi/etc/pihole-updatelists.conf`

The next blocker is no longer discovery. The next blocker is validating the
import path safely before household DNS is moved off the raspi.
