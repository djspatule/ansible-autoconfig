# Architecture Guide

## Big Picture

This repository still contains some older workstation material, but the active
architecture is now intentionally close to the LearnLinuxTV pattern:

- `base` runs on every host
- `server` runs only on server hosts
- workstation hosts are parked out of inventory for now while the common base is
  being cleaned up

The canonical execution entry point is now `local.yml`.

```mermaid
flowchart TD
    A[local.yml] --> B[pre_tasks on all hosts]
    A --> C[base role on all hosts]
    A --> E[server role on server group]
    A --> F[cleanup tasks on all hosts]

    C --> C1[common_packages.yml]
    C --> C2[dotfiles.yml]
    C --> C3[autopull.yml]

    E --> E1[docker.yml]
    E --> E2[mounts.yml]
    E --> E3[homepage.yml]
    E --> E4[bentopdf.yml]
    E --> E5[game_timer.yml]
    E --> E6[nextcloud.yml]
    E --> E7[pihole.yml]
    E --> E8[aumenuilya.yml]
    E --> E9[reverse_proxy.yml]

    E9 --> G[Caddy container]
    E3 --> H[Homepage container]
    E4 --> I[BentoPDF container]
    E5 --> J[game-timer container]
    E6 --> K[Nextcloud container]
    E6 --> L[Nextcloud MariaDB container]
    E7 --> M[Pi-hole container]
    E8 --> N[WordPress container]
    E8 --> O[WordPress MariaDB container]
```

## Top-Level Files

### `local.yml`

Main playbook.

- `all` pre-tasks refresh package metadata for both Arch and Debian-family systems
- `all` hosts run the common `base` role
- `server` hosts then run the server-specific `server` role
- `all` cleanup tasks finish the run

This file is the closest match to the LearnLinuxTV-style structure you referenced.

### `server_core.yml`

Compatibility wrapper.

- It exists so the server path can still be invoked explicitly
- It now simply calls the `server` role
- `local.yml` is the more important entry point

### `hosts`

Static inventory.

- `[server]`: `raspberrypi`, `serverannah`, `archlinux`

The workstation hosts are intentionally removed from the active inventory for now
so the architecture work can focus on the common base plus the server path.

`archlinux` is the disposable VM used as the feedback loop host.

### `ansible.cfg`

Repository-local Ansible defaults.

- inventory file is `hosts`
- logs go to `/var/log/ansible.log`
- retry files are disabled

This matters because `scripts/bootstrap-server.sh` and the autopull helper both export `ANSIBLE_CONFIG` so `ansible-pull` uses repo-local inventory and settings.

### `requirements.yml`

Explicit collection dependencies:

- `community.general`
- `community.docker`

These are needed for modules like `community.general.snap`, `community.general.pacman`, and Docker resource modules.

## Host-Specific Vars

### `host_vars/serverannah`

Real headless Ubuntu server profile.

Defines:

- `ansible_connection: local`
- `autoconfig_branch`
- `autoconfig_playbook`
- which server subservices are enabled
- reverse proxy hostnames and upstreams
- AuMenuIlYA backup source path
- structured storage mount data in `server_storage_mounts`

This file is where the server personality lives.

### `host_vars/archlinux`

VM test profile.

Defines:

- the same local-connection model as `serverannah`
- VM-only hostnames like `*.localtest.me`
- non-conflicting ports like `8081` and `5300`
- enabled services for VM validation

This file exists to prove portability and idempotency without touching the real server.

## The `roles/base` Role

This is now the common foundation for every active host.

### `roles/base/tasks/main.yml`

Like LearnLinuxTV's repo, `base` is the common entrypoint.

It currently imports:

1. `common_packages.yml`
2. `dotfiles.yml`
3. `autopull.yml`

The old desktop-heavy base tasks are still in git history and in the tree, but
they are no longer part of the active `base` execution path.

### `roles/base/tasks/common_packages.yml`

Installs the common cross-distro CLI baseline.

- distro-specific package mapping for Debian and Arch
- shared CLI utilities
- Stow
- optional CLI snaps on Debian-family hosts

### `roles/base/tasks/dotfiles.yml`

First Stow-based dotfiles slice.

- ensure the target user home exists
- clone the public `omarchy-dotfiles` repo into a user-scoped checkout
- back up or hand over a pre-existing `.bashrc`
- run `stow --restow` for the host-selected package list

Current scope is intentionally conservative:

- enabled on `serverannah` and `archlinux`
- first package is `bash`
- risky packages such as `ssh` or Hyprland are not auto-stowed yet

### `roles/base/tasks/autopull.yml`

Installs the recurring `ansible-pull` automation.

- installs `/usr/local/bin/autoconfig-pull`
- installs a `systemd` service and timer
- reloads systemd
- enables the timer

## The `roles/server` Role

This is now the main server orchestration role.

### `roles/server/tasks/main.yml`

Dispatch file.

It imports the server task files in a flat and explicit order:

1. `docker.yml`
2. `mounts.yml`
3. `homepage.yml`
4. `bentopdf.yml`
5. `game_timer.yml`
6. `nextcloud.yml`
7. `pihole.yml`
8. `aumenuilya.yml`
9. `reverse_proxy.yml`

Each optional service is guarded by a host var such as `server_homepage_enabled`.

### `roles/server/defaults/main.yml`

Server role defaults.

This file is important because it holds:

- server-specific Docker package maps
- service defaults for Homepage, BentoPDF, game-timer, Nextcloud, Pi-hole, AuMenuIlYA, and reverse proxy
- secret file locations
- network names, ports, and container names

This is the main schema of the server role.

### `roles/server/tasks/docker.yml`

Server-specific platform setup.

Responsibilities:

- assert supported OS family for Docker packages
- install Docker from distro packages
- enable and start Docker

The shared CLI baseline no longer lives here; it moved into `roles/base`.

### `roles/server/tasks/homepage.yml`

Deploys Homepage.

- creates the app directory
- deploys a stow-like config tree from `files/homepage/opt/homepage/config/`
- creates/uses the shared Docker network
- starts the Homepage container

### `roles/server/tasks/mounts.yml`

Storage foundation for hosts with extra disks.

Responsibilities:

- create the mount point directories
- manage the corresponding `/etc/fstab` entries
- ensure the filesystems are mounted now, not just declared for later boot

This task file is driven by `server_storage_mounts` in host vars.

### `roles/server/tasks/bentopdf.yml`

Deploys BentoPDF as a simple Dockerized service on the shared network.

### `roles/server/tasks/game_timer.yml`

Deploys the second website.

- deploys a vendored static snapshot from `files/game-timer/site/`
- serves it through `nginx:alpine`
- exposes it only through the shared Docker network by default

This is the current pattern for plain static sites.

### `roles/server/tasks/nextcloud.yml`

Deploys Nextcloud as a Dockerized app with MariaDB.

- creates persistent app, DB, and data directories
- generates DB and admin secrets on the target host
- runs MariaDB and Nextcloud containers
- configures trusted domains and reverse-proxy settings with `occ`

This service is designed around `serverannah` using `/mnt/SSD_1TO/nextcloud` as the main persistent storage root.

### `roles/server/tasks/pihole.yml`

Deploys Pi-hole.

- manages the Pi-hole config and secret directories
- generates the web password on the target host
- starts the Pi-hole container
- relies on Caddy only for the admin UI, not for DNS traffic itself

### `roles/server/tasks/aumenuilya.yml`

Deploys the WordPress site.

Responsibilities:

- validate the host-local backup source exists
- sync `wp-content`
- restore `.htaccess` and `ads.txt`
- create target-side DB secrets
- run MariaDB container
- import SQL only if the DB is not already initialized
- run WordPress container
- rewrite URLs with WP-CLI only when needed

This is not a simple “docker up” file. It is restore automation encoded in Ansible.

### `roles/server/tasks/reverse_proxy.yml`

Deploys Caddy.

- creates config/data directories
- renders the `Caddyfile`
- runs the Caddy container
- restarts the container when the config changes

### `roles/server/templates/Caddyfile.j2`

Host-driven reverse proxy config.

Each site entry in `server_reverse_proxy_sites` can either:

- proxy to an upstream container
- redirect to a canonical hostname

## `files/`

Static payloads managed by Ansible.

Most important current subtree:

- `files/homepage/opt/homepage/config/`

This is intentionally close to a stow-like package layout already, which makes future reuse easier.

There are also older workstation-oriented payloads still present, such as:

- shell config files
- Espanso snippets
- Betterbird profile material
- rclone files

Those are not yet normalized into the newer server path.

## `scripts/bootstrap-server.sh`

First-run bootstrap helper for fresh servers.

Responsibilities:

- detect Debian-family vs Arch-family host
- install `git` and `ansible-core`
- clone or update the repo
- install required collections
- export `ANSIBLE_CONFIG`
- run `ansible-pull`

This is the bridge between a blank server and a self-managing one.

## `backups/`

Repository-side capture of important host configuration.

Currently added:

- `backups/serverannah/etc/fstab`

This is a raw reference copy, not yet an applied task.

## Legacy Areas Still Present

The repo still contains older layers that matter:

- `roles/base/`
- `roles/workstation/`
- older `files/` payloads
- `group_vars/all`

These are kept because the repository is being refactored incrementally, not rewritten from scratch.

## Current Execution Logic

The practical flow is:

1. `ansible-pull` runs `local.yml`
2. every active host enters `roles/base/tasks/main.yml`
3. server hosts then enter `roles/server/tasks/main.yml`
4. host vars decide which server services are active
5. Caddy fronts whichever services are enabled
6. `autopull` is already installed by the common base role

## Dotfiles Direction

This repo is not yet the dotfiles source of truth, but it is now structured so that can happen gradually.

The safest future path is:

1. move dotfiles into package-like directories under this repo
2. install `stow` with Ansible
3. have Ansible call `stow` on selected packages per host profile
4. keep secrets and highly host-specific files out of the generic stow set

That keeps Ansible as the orchestrator and Stow as the placement mechanism.

The first real implementation of that path now exists in `roles/base/tasks/dotfiles.yml`, but it still points at the external public repo until the packages are migrated into this repository.
