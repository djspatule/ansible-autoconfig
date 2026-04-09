# Project Guidelines

## Purpose

- Build a long-lived `ansible-pull` repository that can configure different machines after a reinstall.
- Keep the server path boring, idempotent, and portable across more than one Linux family.
- Use the current Arch VM as a fast feedback loop before touching `serverannah`.

## Current Server Playbooks

- `local.yml`: the main entry point again. It runs `base` for workstations and `server` for hosts in the `server` inventory group.
- `server_core.yml`: compatibility playbook that now simply runs the `server` role.

## Current Role Boundaries

- `roles/server`: the LearnLinuxTV-style aggregation role. Its task files are `base`, `mounts`, `homepage`, `bentopdf`, `dotfiles`, `game_timer`, `nextcloud`, `pihole`, `aumenuilya`, `reverse_proxy`, and `autopull`.

## Isolation Strategy

- The old `local.yml` and legacy desktop/server roles are kept intact.
- The old desktop-oriented `base` role now stays on workstation hosts.
- The server path is isolated inside `roles/server/tasks/*.yml`, so the architecture matches the original repo shape while still keeping server-only logic away from desktop tasks.

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

- The disposable Arch VM is represented as `archlinux` in `hosts`.
- `host_vars/archlinux` keeps the VM on the normal inventory path instead of using a fake localhost-only workflow.
- Use the VM to prove portability and idempotency before applying changes on `serverannah`.
- Pi-hole binds `5300` on the VM so DNS can be tested without stealing the VM host's normal resolver port.

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
