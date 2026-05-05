# Project Guidelines

## Purpose

- Build a long-lived `ansible-pull` repository that can configure different machines after a reinstall.
- Keep the server path boring, idempotent, and portable across more than one Linux family.
- Use the current Arch VM as a fast feedback loop before touching `serverannah`.

## Current Server Playbooks

- `local.yml`: the main entry point again. It runs `base` for all active hosts and `server` for hosts in the `server` inventory group.
- `server_core.yml`: compatibility playbook that now simply runs the `server` role.

## Current Role Boundaries

- `roles/base`: the common role. It now owns shared packages, the first Stow-based dotfiles slice, and recurring `ansible-pull` automation.
- `roles/server`: the LearnLinuxTV-style specialization role. Its task files are `docker`, `mounts`, `homepage`, `bentopdf`, `game_timer`, `nextcloud`, `pihole`, `aumenuilya`, and `reverse_proxy`.

## Isolation Strategy

- The old workstation-oriented base leftovers were removed so the active path now focuses on `base` plus `server` only.
- Workstation hosts are removed from the current inventory until the common base is fully cleaned up.
- The server path is isolated inside `roles/server/tasks/*.yml`, so the architecture now matches the original LearnLinuxTV split more closely.

## First-Run Bootstrap

Use the bootstrap script when a new server does not have Ansible yet.

```bash
sudo ./scripts/bootstrap-server.sh
```

Optional environment overrides:

```bash
sudo AUTOCONFIG_BRANCH=server-bootstrap AUTOCONFIG_PLAYBOOK=server_core.yml ./scripts/bootstrap-server.sh
```

The bootstrap script currently supports Debian-family and Arch-family systems.

## Manual Test Commands

Run the full server stack locally on a machine already prepared for Ansible:

```bash
sudo ansible-playbook -i hosts --limit serverannah server_core.yml
```

Or use the canonical entry point directly:

```bash
sudo ansible-playbook -i hosts --limit serverannah local.yml
```

Run through `ansible-pull` on a real target host:

```bash
sudo ansible-pull -U https://github.com/djspatule/ansible-autoconfig.git -C server-bootstrap -d /opt/ansible-pull server_core.yml
```

Test the reverse proxy on the Arch VM with GET requests and host headers:

```bash
curl -H 'Host: homepage.localtest.me' http://127.0.0.1:8081/
curl -H 'Host: bentopdf.localtest.me' http://127.0.0.1:8081/
curl -H 'Host: game-timer.localtest.me' http://127.0.0.1:8081/
curl -H 'Host: pihole.localtest.me' http://127.0.0.1:8081/admin/
```

Test Pi-hole DNS itself on the Arch VM:

```bash
sudo docker exec pihole nslookup pi-hole.net 127.0.0.1
```

## VM Feedback Loop

- The old disposable Arch VM was retired and removed from the active inventory.
- Validate changes on `serverannah` deliberately before production cutover.

## Known Caveats

- `ansible-pull` still emits a hostname-pattern warning during its internal git step. The actual playbook run is what matters.
- `community.general` and `community.docker` are required and declared in `requirements.yml`.
- Homepage config is stored under `files/homepage/opt/homepage/config/` so it can later be repackaged in a stow-like structure if needed.

## Raspi Clues

- Existing compose files on the raspi live under `/home/pi/docker/`.
- Confirmed current service directories:
  - `homepage/`
  - `nextcloud/`
  - `npm/`
  - `frigate/`
- `tabletop-timer.com` appears in the raspi nginx logs, which supports keeping it as the likely public hostname for `game-timer`.
- `dinnizer.com` appears in an old Nginx Proxy Manager config, but there is no verified live Dinnizer deployment on the raspi to migrate directly.
- The old Nextcloud compose contains plaintext credentials, so future migration work should treat the raspi files as discovery material, not as files to copy verbatim into git.
