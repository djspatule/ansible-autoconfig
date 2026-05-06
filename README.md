# Ansible Autoconfig

This repository is the family `ansible-pull` source of truth.

The active goal is simple:

- one main entry point: `local.yml`
- one common role: `roles/base`
- one server role: `roles/server`
- code that stays readable by a non-expert
- host-specific state stored in obvious places
- configuration changed in git first, not directly on the machine

## Design Rules

- Prefer small Ansible modules over clever shell logic.
- Keep one source of truth per concern.
- Do not encode migration hacks for old machines unless they are still truly needed.
- If a value is host-specific, keep it in `host_vars/serverannah`.
- If a file is the real source of truth, store it in `files/` and copy it.

## Active Layout

- `local.yml`: main playbook
- `hosts`: active inventory
- `group_vars/all`: tiny shared defaults only
- `host_vars/serverannah`: server-specific switches, domains, URLs, and hardware paths
- `roles/base`: packages, Starship shell init, dotfiles via Stow, ansible-pull automation
- `roles/server`: Docker services, reverse proxy, Pi-hole, Nextcloud, Frigate, fail2ban, storage bootstrap
- `files/dotfiles/`: Stow packages actually managed by this repo
- `files/serverannah/etc/fstab`: source of truth for `serverannah` storage mounts
- `files/pihole/policy/`: Pi-hole adlists and allowlist imported by Ansible

## Current Entry Points

Run locally against the active inventory:

```bash
sudo ansible-playbook -i hosts --limit serverannah local.yml
```

Run with `ansible-pull` on the target machine:

```bash
sudo ansible-pull -U https://github.com/djspatule/ansible-autoconfig.git -C server-bootstrap -d /opt/ansible-pull local.yml
```

Bootstrap a fresh server that does not have Ansible yet:

```bash
sudo ./scripts/bootstrap-server.sh
```

Dry-run a local checkout when testing:

```bash
sudo ansible-playbook -i hosts --limit serverannah local.yml --check
```

## Why `requirements.yml` Stays

`requirements.yml` is not just documentation.

It is the executable dependency manifest used by the bootstrap script and the
managed `autoconfig-pull` helper to install required collections such as:

- `community.general`
- `community.docker`
- `ansible.posix`

Keeping that in code is simpler and safer than hoping the README stays in sync.

## What `group_vars/all` Still Does

Very little, by design.

It now only holds shared defaults that are still useful for the active code:

- `desktop_user`
- `ansible_python_interpreter`

Anything more specific belongs in host vars or role defaults.

## Storage Model

Storage was simplified on purpose.

Instead of rebuilding mount lines from structured YAML, the repo now ships the
target host's `fstab` directly:

- source: `files/serverannah/etc/fstab`
- deployed to: `/etc/fstab`

The server role then:

1. copies the file
2. creates the mount points declared in it
3. runs `mount -a`

This is less generic, but easier to read and maintain.

## Dotfiles Model

Dotfiles are handled with:

- Ansible as orchestrator
- Stow as symlink engine

Only curated packages that already live in `files/dotfiles/` should be enabled.
Right now the active set is intentionally small.

## Pi-hole Source Of Truth

Pi-hole policy import now reads from:

- `files/pihole/policy/adlists_enabled.txt`
- `files/pihole/policy/allowlist_exact.txt`

Raw backups are not meant to be the long-term source of truth.

## Serverannah Notes

`serverannah` is the current production target.

Important host-specific values live in `host_vars/serverannah`, including:

- enabled services
- public domains
- Pi-hole mode
- hardware-specific device paths
- backup source paths still needed for migration

## Conventions For Future Changes

- package lists should stay in role defaults
- hostnames, domains, and paths should stay in host vars
- static config files should go under `files/`
- comments should explain why a choice exists, not narrate every line

## Known Reality

- the old raspi still matters as migration knowledge, but should not dictate the final design
- public DNS and NAT still need deliberate validation before full production cutover
- `ansible-pull` may print a hostname-pattern warning during its internal git step; the actual playbook result matters more than that warning
