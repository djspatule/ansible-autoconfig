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
    ./scripts/seed-uptime-kuma.py --url https://status.dinnizer.com [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
DEFAULT_HOST_VARS = REPO / "host_vars" / "serverannah"
CREDENTIALS_FILE = "/etc/ansible/secrets/uptime-kuma-credentials"
CADDY_PASSWORD_FILE = "/etc/ansible/secrets/caddy-shared-password"


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


def plan_monitor(site: dict, basic_auth_user: str, basic_auth_password: str | None) -> dict:
    """Turn one reverse-proxy site into the monitor we want for it."""
    hostname = site["hostname"]
    plan: dict = {
        "name": hostname,
        "url": f"https://{hostname}/",
        # 60s is plenty for a homelab and keeps the SQLite heartbeat table small.
        "interval": 60,
        # Two retries before alerting, so one dropped packet is not an incident.
        "maxretries": 2,
        "timeout": 30,
        # Warn before a certificate expires. This is half the reason the whole
        # thing exists: a silently unrenewed cert takes a site down with no
        # warning at all.
        "expiryNotification": True,
        # Nextcloud and Jellyfin answer / with a 302 to their login page, which
        # is a perfectly healthy response, so 3xx is accepted everywhere.
        "accepted_statuscodes": ["200-299", "300-399"],
    }

    if site.get("redirect_to"):
        # A redirect host is healthy when it redirects. Following it would test
        # the *target* instead and hide a broken redirect, so cap redirects at 0.
        plan["maxredirects"] = 0
        return plan

    if site.get("basic_auth"):
        if basic_auth_password:
            # Authenticate so the check reaches the application. Without this the
            # monitor would only ever see Caddy's 401 and would report green with
            # a dead service behind it.
            plan["_basic_auth"] = (basic_auth_user, basic_auth_password)
        else:
            # No password available: settle for proving DNS, TLS and Caddy are
            # alive by treating the auth challenge itself as success. This does
            # NOT check the application behind the gate.
            plan["accepted_statuscodes"] = ["200-299", "300-399", "401"]
    return plan


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="https://status.dinnizer.com", help="Uptime Kuma base URL")
    ap.add_argument("--host-vars", type=Path, default=DEFAULT_HOST_VARS)
    ap.add_argument("--basic-auth-user", default="lion", help="user for basic-auth'd sites")
    ap.add_argument("--dry-run", action="store_true", help="print the plan and exit, touching nothing")
    args = ap.parse_args()

    sites = load_sites(args.host_vars)
    if not sites:
        sys.exit(f"No server_reverse_proxy_sites found in {args.host_vars}")

    caddy_password = read_secret(CADDY_PASSWORD_FILE)
    if not caddy_password:
        print(
            f"note: {CADDY_PASSWORD_FILE} unreadable — basic-auth'd sites will be "
            "monitored by accepting their 401 instead of checking behind it.",
            file=sys.stderr,
        )

    plans = [plan_monitor(s, args.basic_auth_user, caddy_password) for s in sites]

    if args.dry_run:
        print(f"{len(plans)} monitors planned from {args.host_vars.name}:\n")
        for p in plans:
            auth = " (authenticated)" if p.get("_basic_auth") else ""
            codes = ",".join(p.get("accepted_statuscodes", []))
            print(f"  {p['name']:26s} {p['url']:42s} [{codes}]{auth}")
        return 0

    # Imported late so --dry-run needs no dependency and no network.
    from uptime_kuma_api import AuthMethod, UptimeKumaApi

    username, password = kuma_credentials()
    api = UptimeKumaApi(args.url)
    try:
        api.login(username, password)
        existing = {m["name"] for m in api.get_monitors()}
        created = skipped = 0
        for p in plans:
            if p["name"] in existing:
                print(f"  skip    {p['name']} (already exists)")
                skipped += 1
                continue
            # _basic_auth is our own marker; translate it into the library's
            # parameters here rather than importing the enum at module scope.
            creds = p.pop("_basic_auth", None)
            if creds:
                p["authMethod"] = AuthMethod.HTTP_BASIC
                p["basic_auth_user"], p["basic_auth_pass"] = creds
            api.add_monitor(type="http", **p)
            print(f"  created {p['name']}")
            created += 1
        print(f"\n{created} created, {skipped} already present, {len(plans)} total")
    finally:
        api.disconnect()
    return 0


if __name__ == "__main__":
    sys.exit(main())
