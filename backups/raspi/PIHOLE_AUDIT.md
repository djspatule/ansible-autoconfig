# Raspi Pi-hole Audit

## Status

This audit is incomplete but still useful.

What was readable through the mounted raspi filesystem:

- `/etc/pihole/pihole.toml`
- `/etc/pihole-updatelists.conf`

What was *not* readable from the current mount because the files are owned by the
`onepassword` group and this environment does not have local sudo:

- `/etc/pihole/adlists.list`
- `/etc/pihole/local.list`
- `/etc/pihole/hosts/custom.list`
- `/etc/pihole/dns-servers.conf`
- `/etc/pihole/gravity.db`
- `/etc/pihole/pihole-FTL.db`
- `/etc/pihole/migration_backup_v6/*`

Because of that, the current server role can be aligned with the visible raspi
behavior, but it cannot yet claim to preserve the full allow/block/custom-DNS
state of the live Pi-hole install.

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

## Cutover Assessment

Safe conclusions:

- `serverannah` Pi-hole should default to Google upstreams, `LOCAL` listening,
  and `lan` domain to match the visible raspi settings.
- The update-lists helper is not currently pulling any remote list sources.

Unsafe assumptions:

- adlists are complete
- local DNS overrides are complete
- whitelist/blacklist rules are complete
- regex rules are complete

Those may still live in unreadable Pi-hole database or root-only files.

## Recommendation

Do **not** cut over the household DNS from raspi to `serverannah` until one of
these happens:

1. the root-only Pi-hole files become readable through the raspi mount
2. you export the Pi-hole configuration from the raspi UI/CLI manually
3. the raspi itself becomes reachable over SSH with privileges sufficient to read
   `/etc/pihole/` and the Pi-hole databases

Until then, `serverannah` can host a Pi-hole service skeleton, but it should not
be treated as a full replacement for the current production Pi-hole.
