#!/usr/bin/env python3
"""Seed Uptime Kuma monitors from the same site list Caddy is generated from.

WHY THIS IS A SCRIPT AND NOT AN ANSIBLE TASK
--------------------------------------------
Uptime Kuma 1.x has no REST API for monitors — `/api/monitors` returns the
single-page-app shell, not data. Everything goes over socket.io, reached here
through the unofficial `uptime-kuma-api` library. That is fine for a seeder you
run occasionally and watch, and wrong for something the nightly ansible-pull
depends on: an upstream change would break the pull for every host at once.

So this is deliberately a one-shot tool, not config management. Re-running it is
safe (existing monitors are left alone), but it will not remove or reconcile
monitors you have edited in the UI. The UI stays the source of truth for
monitors; this just saves the initial clicking.

SOURCE OF TRUTH
---------------
Monitors come from `server_reverse_proxy_sites` in host_vars — the very list
Caddy's config is rendered from — so a site cannot exist in the proxy and be
silently unmonitored.

CREDENTIALS
-----------
Kuma admin login, from the environment or a root-only file:

    KUMA_USERNAME / KUMA_PASSWORD, or
    /etc/ansible/secrets/uptime-kuma-credentials  (two lines: user, then password)

Basic-auth'd sites are monitored *through* their auth using the shared Caddy
password, so the check reaches the real application instead of stopping at
Caddy's 401 and reporting a healthy gate in front of a dead service.

USAGE
    ./scripts/helpers/seed-uptime-kuma.py --url https://status.dinnizer.com [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml

# scripts/helpers/<this file> -> up two levels is the repository root.
REPO = Path(__file__).resolve().parents[2]
DEFAULT_HOST_VARS = REPO / "host_vars" / "serverannah"
CREDENTIALS_FILE = "/etc/ansible/secrets/uptime-kuma-credentials"
NTFY_TOPIC_FILE = "/etc/ansible/secrets/notify-topic"


def load_sites(host_vars: Path) -> list[dict]:
    data = yaml.safe_load(host_vars.read_text()) or {}
    return data.get("server_reverse_proxy_sites", []) or []


def read_secret(path: str) -> str | None:
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def kuma_credentials() -> tuple[str, str]:
    user = os.environ.get("KUMA_USERNAME")
    password = os.environ.get("KUMA_PASSWORD")
    if user and password:
        return user, password
    blob = read_secret(CREDENTIALS_FILE)
    if blob and len(blob.splitlines()) >= 2:
        lines = blob.splitlines()
        return lines[0].strip(), lines[1].strip()
    sys.exit(
        f"No Kuma credentials. Set KUMA_USERNAME and KUMA_PASSWORD, or put the\n"
        f"username and password on two lines in {CREDENTIALS_FILE} (chmod 600)."
    )


def plan_monitors(site: dict) -> list[dict]:
    """Turn one reverse-proxy site into the monitors we want for it.

    Two monitors, because they answer different questions and fail
    independently:

      * the public one proves DNS, TLS, the certificate and Caddy are alive for
        that exact hostname — but it stops at the auth gate on protected sites;
      * the internal one talks to the container directly over the Docker
        network, proving the application itself is serving — and needs no
        credentials at all, because it never passes through Caddy.

    That second point is the important one. An earlier version authenticated the
    public check with the shared Caddy password, which meant Uptime Kuma held a
    copy of it: rotating that password would silently break seven monitors until
    someone remembered to re-seed. Checking the app from inside the network
    removes the copy, so there is nothing left to keep in sync.
    """
    hostname = site["hostname"]
    path = site.get("monitor_path", "/")

    base = {
        "interval": 60,
        # Two retries before alerting, so one dropped packet is not an incident.
        "maxretries": 2,
        "timeout": 30,
    }

    public = dict(
        base,
        name=hostname,
        url=f"https://{hostname}{path}",
        # Warn before a certificate expires. This is half the reason the whole
        # thing exists: a silently unrenewed cert takes a site down with no
        # warning at all.
        expiryNotification=True,
        # 3xx because Nextcloud and Jellyfin answer / with a redirect to their
        # login page, which is healthy. 401 because a protected site answering
        # "authentication required" proves the edge works — the app behind it is
        # the internal monitor's job, not this one's.
        accepted_statuscodes=["200-299", "300-399", "401"],
    )
    if site.get("redirect_to"):
        # A redirect host is healthy when it redirects. Following it would test
        # the *target* instead and hide a broken redirect, so cap redirects at 0.
        public["maxredirects"] = 0
        # Nothing behind it to check separately.
        return [public]

    monitors = [public]

    upstream = site.get("upstream")
    if upstream:
        # Skip upstreams that are not plain container:port (e.g. an https://
        # backend or one templated to a LAN IP) — those are not reachable by
        # name from the seeder's network and would monitor the wrong thing.
        if "://" not in upstream:
            monitors.append(dict(
                base,
                name=f"{hostname} [app]",
                url=f"http://{upstream}{path}",
                accepted_statuscodes=["200-299", "300-399"],
                # An internal hop has no certificate to expire.
                expiryNotification=False,
            ))
    return monitors


def ensure_ntfy_notification(api, topic: str, base_url: str, name: str) -> int | None:
    """Create the ntfy notification and attach it to every monitor.

    `applyExisting=True` is what makes this worth automating: it wires the
    notification onto all existing monitors in one call, and `isDefault=True`
    means every monitor created later inherits it. Without that, fifteen
    monitors detect failures and have nowhere to report them, which is the same
    silent-failure problem this whole exercise started from.
    """
    # Match on type, not name: a notification created by hand in the UI will
    # have whatever name the operator chose, and creating a second ntfy target
    # would double every alert rather than fix anything.
    for existing in api.get_notifications():
        if existing.get("type") == "ntfy" or "ntfy" in str(existing.get("name", "")).lower():
            nid = existing["id"]
            print(f"  ntfy notification already present: '{existing.get('name')}' (id={nid})")
            # A notification created by hand defaults to isDefault=False, which
            # means monitors created later silently do NOT inherit it. That is
            # the quiet version of having no alerting at all, so force it on.
            if not existing.get("isDefault"):
                api.edit_notification(nid, isDefault=True, applyExisting=True)
                print("    set as default so new monitors inherit it")
            return nid
    return None
    result = api.add_notification(
        name=name,
        type="ntfy",
        isDefault=True,
        applyExisting=True,
        ntfyserverurl=base_url,
        ntfytopic=topic,
        ntfyPriority=4,
        ntfyAuthenticationMethod="none",
    )
    print(f"  created notification '{name}' and applied it to all monitors")
    return result.get("id")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="https://status.dinnizer.com", help="Uptime Kuma base URL")
    ap.add_argument("--host-vars", type=Path, default=DEFAULT_HOST_VARS)
    ap.add_argument("--dry-run", action="store_true", help="print the plan and exit, touching nothing")
    ap.add_argument("--replace", action="store_true",
                    help="delete and recreate planned monitors that already exist "
                         "(use after changing how monitors are built)")
    ap.add_argument("--ntfy-base-url", default="https://ntfy.sh")
    ap.add_argument("--notification-name", default="ntfy")
    ap.add_argument("--skip-notification", action="store_true")
    args = ap.parse_args()

    sites = load_sites(args.host_vars)
    if not sites:
        sys.exit(f"No server_reverse_proxy_sites found in {args.host_vars}")

    plans = [m for site in sites for m in plan_monitors(site)]

    if args.dry_run:
        print(f"{len(plans)} monitors planned from {args.host_vars.name}:\n")
        for m in plans:
            codes = ",".join(m.get("accepted_statuscodes", []))
            cert = " +cert" if m.get("expiryNotification") else ""
            print(f"  {m['name']:34s} {m['url']:46s} [{codes}]{cert}")
        return 0

    # Imported late so --dry-run needs no dependency and no network.
    from uptime_kuma_api import UptimeKumaApi

    username, password = kuma_credentials()
    api = UptimeKumaApi(args.url)
    try:
        api.login(username, password)

        notification_id = None
        if not args.skip_notification:
            topic = read_secret(NTFY_TOPIC_FILE)
            if topic:
                notification_id = ensure_ntfy_notification(
                    api, topic, args.ntfy_base_url, args.notification_name)
            else:
                print(f"  note: no ntfy topic at {NTFY_TOPIC_FILE}; skipping notification setup",
                      file=sys.stderr)

        existing = {m["name"]: m["id"] for m in api.get_monitors()}
        created = replaced = skipped = 0
        for m in plans:
            if m["name"] in existing:
                if not args.replace:
                    print(f"  skip     {m['name']} (already exists)")
                    skipped += 1
                    continue
                api.delete_monitor(existing[m["name"]])
                api.add_monitor(type="http", **m)
                print(f"  replaced {m['name']}")
                replaced += 1
                continue
            api.add_monitor(type="http", **m)
            print(f"  created  {m['name']}")
            created += 1
        # isDefault only covers monitors created *after* it was set, and
        # applyExisting is a one-shot at write time, so neither helps a monitor
        # created in between. Sweep every monitor at the end instead: an alert
        # nobody receives is indistinguishable from no monitoring at all.
        if notification_id is not None:
            attached = 0
            for mon in api.get_monitors():
                if notification_id not in (mon.get("notificationIDList") or []):
                    api.edit_monitor(mon["id"], notificationIDList=[notification_id])
                    attached += 1
            if attached:
                print(f"  attached the ntfy notification to {attached} monitor(s)")

        print(f"\n{created} created, {replaced} replaced, {skipped} unchanged, {len(plans)} total")
    finally:
        api.disconnect()
    return 0


if __name__ == "__main__":
    sys.exit(main())
