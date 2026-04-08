# Project Guidelines

## Purpose

- Build a long-lived `ansible-pull` repository that can configure different machines after a reinstall.
- Keep the server path boring, idempotent, and portable across more than one Linux family.
- Use the current Arch VM as a fast feedback loop before touching `serverannah`.

## Current Server Playbooks

- `server_bootstrap.yml`: install the base CLI set, Docker, and distro-specific dependencies.
- `server_homepage.yml`: deploy Homepage on port `3000`.
- `server_bentopdf.yml`: deploy BentoPDF on port `8080`.
- `server_core.yml`: the main server entry point. It always runs `server_base` and the recurring pull timer, and it adds Homepage or BentoPDF when the host enables them.

## Current Role Boundaries

- `roles/server_base`: package manager differences, Docker installation, and base server CLI tools.
- `roles/server_homepage`: deploy Homepage config and container.
- `roles/server_bentopdf`: deploy BentoPDF container.
- `roles/server_autopull`: install the helper script and `systemd` timer that re-runs the configuration daily.

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

Run through `ansible-pull` on a real target host:

```bash
sudo ansible-pull -U https://github.com/djspatule/ansible-autoconfig.git -C server-bootstrap -d /opt/ansible-pull server_core.yml
```

## VM Feedback Loop

- The disposable Arch VM is represented as `archlinux` in `hosts`.
- `host_vars/archlinux` keeps the VM on the normal inventory path instead of using a fake localhost-only workflow.
- Use the VM to prove portability and idempotency before applying changes on `serverannah`.

## Known Caveats

- `ansible-pull` still emits a hostname-pattern warning during its internal git step. The actual playbook run is what matters.
- `community.general` and `community.docker` are required and declared in `requirements.yml`.
- Homepage config is stored under `files/homepage/opt/homepage/config/` so it can later be repackaged in a stow-like structure if needed.
