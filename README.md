# Ansible Autoconfig

![Ansible Logo](https://www.learnlinux.tv/wp-content/uploads/2020/12/ansible-e1607524003363.png)

This repository is based on the code that Jay Lacroix (LearnLinuxTV) worked on
from his [Ansible Desktop tutorial on Youtube](https://youtu.be/gIDywsGBqf4).

Additionnal inspiration could be taken from
[Jeef Geerling's work on Ansible](https://ansible.jeffgeerling.com)

It was improved with the Ansible-pull tutorial and then coding was improved with
ChatGPT's Codex (via opencode and pi.dev).

## Usage

objective is to have something that can be run easily on a new machine or not
(idempotent) with:

> sudo ansible-pull -U <https://github.com/djspatule/ansible-autoconfig.git>
> --vault-password-file ~/secret.txt -C main

in test mode, to avoid having to "git push" each modification in order to test
it locally on a development machine where the repo is present (because i'm
currently working on it for instance), use:

> sudo ansible-pull -U "~/Documents/ansible-autoconfig/" --check

or

> sudo ansible-playbook -i "localhost," -c local local.yml --check

_remember that ansible-pull is just a wrapper for ansible-playbook....so both
cmds are kinda similar ... and the check option allows to test on a system
without implementing anything ('dry run')._

## ToDo

- [x] initiate base role and server role
- [ ] finish implementing a base and server roles that work on fresh arch and
      ubuntu machines
- [ ] implement workstation role
- [ ] implement kids role
- [ ] find inspiration in
      [jaylacroix's code](https://github.com/LearnLinuxTV/personal_ansible_desktop_configs/tree/main)
      and eventually omakub's code or Jeff Geerling's code.
- [ ] use tags to only test/execute parts of the ansible-autoconfig script...
      that should accelerate dev/debug and limit need for protection against
      downloads (to preserve bandwidth).

### Guidelines for coding agents

#### Objectives

- Use ansible-pull (sudo ansible-pull -U
  <https://github.com/djspatule/ansible-autoconfig.git> --vault-password-file
  ~/secret.txt -C main) to automate the set-up of any of my family’s computer if
  they ever have to be reinstalled from scratch (on the same or different
  hardware).
- The set-up must be idem-potent so that it can be set to run automatically once
  a day on each of these machine (via a crontab job or else)
- I need to be able to “test” on a virtual machine. 

My dotfiles are currently
  specific to Omarchy and managed with stow
  (<https://github.com/djspatule/omarchy-dotfiles>)... I want to transition from the dotfiles specific repo to this repo and have stow managed by ansible as part of the setup. Maintenance of the files need to be feasible and easy.
- Use this for inspiration of structuration, etc.
  <https://github.com/LearnLinuxTV/personal_ansible_desktop_configs/tree/main>
- I’m writing this code also as an opportunity to learn about ansible,
  GNU/linux, neovim, opencode and other coding agents (and vibecoding in
  general), tmux, git, networking, etc. Thus explain all the code, design choices, structure, etc in that perspective... 
- I would ideally like to lay here the foundations of an auto-config ansible setup that will
  be still valid and usable in 20 years….(comment your code profusely in that regard)
- The short term priority is to work on the server but the rest will be addressed as well (kids computer, adult's workstations, etc.).

#### Roles

- Server (Serverannah) destined to become a homelab that runs Ubuntu server
  25.10 (headless Optiplex 3070, accessed via SSH) : It is running both natively
  (on bare metal) an Nginx server to host 3 websites (including a complex
  wordpress) and more to come. It's also DNS Filtering with pi-hole (installed
  on bare metal). last, it's running multiple docker services such as frigate
  for cameras, N8N, Odoo, bentopdf, Plex, Timeshift (to secure backups on 1
  master and 3 different external disks copies), Nextcloud (to manage my data
  and make it accessible to the whole family) and the like. For now, those
  functions are managed on a raspi 4B (192.168.1.100) that should be retired
  soon. You don’t have to keep on serverannah things as they were on the raspi.
  It’s a good opportunity to “improve”.
- Kids are running Linux Mint (xfce but switch to cinnamon is envisaged) on a
  very old macbook. Their goal is gaming and learning. Parental control has to
  be strict
- “Mac” is my wife’s computer (not much to set-up there, she mostly works in a
  browser + GDrive and Spotify)
- Laptop is on Omarchy (hyprland) but could be switched to KDE or Gnome on Arch
  or even be switched to an Debian/Ubuntu distro

#### Extra instructions

- ask whenever in doubt and ask for feedback (i can run commands for you, etc.)
- verify your work as much as possible
- remember as much as you can of these instructions and the other instructions
  to come
- Create a “guidelines.md” inside the directory to describe everything the
  project is about, how it works, terminal commands, etc. Templates on github….

#### Do not do

- do not change code without explaining
- do not change multiples files at once when not strictly connected to the same
  taks/objective at hand

## Agent written readme

This repository is the family `ansible-pull` source of truth.

The active goal is simple:

- one main entry point: `local.yml`
- one common role: `roles/base`
- one server role: `roles/server`
- code that stays readable by a non-expert
- host-specific state stored in obvious places
- configuration changed in git first, not directly on the machine

### Design Rules

- Prefer small Ansible modules over clever shell logic.
- Keep one source of truth per concern.
- Do not encode migration hacks for old machines unless they are still truly
  needed.
- If a value is host-specific, keep it in `host_vars/serverannah`.
- If a file is the real source of truth, store it in `files/` and copy it.

### Active Layout

- `local.yml`: main playbook
- `hosts`: active inventory
- `group_vars/all`: tiny shared defaults only
- `host_vars/serverannah`: server-specific switches, domains, URLs, and hardware
  paths
- `roles/base`: packages, Starship shell init, dotfiles via Stow, ansible-pull
  automation
- `roles/server`: Docker services, reverse proxy, Pi-hole, Nextcloud, Frigate,
  fail2ban, storage bootstrap
- `files/dotfiles/`: Stow packages actually managed by this repo
- `files/serverannah/etc/fstab`: source of truth for `serverannah` storage
  mounts
- `files/pihole/policy/`: Pi-hole adlists and allowlist imported by Ansible

### Current Entry Points

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

### Why `requirements.yml` Stays

`requirements.yml` is not just documentation.

It is the executable dependency manifest used by the bootstrap script and the
managed `autoconfig-pull` helper to install required collections such as:

- `community.general`
- `community.docker`
- `ansible.posix`

Keeping that in code is simpler and safer than hoping the README stays in sync.

### What `group_vars/all` Still Does

Very little, by design.

It now only holds shared defaults that are still useful for the active code:

- `desktop_user`
- `ansible_python_interpreter`

Anything more specific belongs in host vars or role defaults.

### Storage Model

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

### Dotfiles Model

Dotfiles are handled with:

- Ansible as orchestrator
- Stow as symlink engine

Only curated packages that already live in `files/dotfiles/` should be enabled.
Right now the active set is intentionally small.

### Pi-hole Source Of Truth

Pi-hole policy import now reads from:

- `files/pihole/policy/adlists_enabled.txt`
- `files/pihole/policy/allowlist_exact.txt`

Raw backups are not meant to be the long-term source of truth.

### Serverannah Notes

`serverannah` is the current production target.

Important host-specific values live in `host_vars/serverannah`, including:

- enabled services
- public domains
- Pi-hole mode
- hardware-specific device paths
- backup source paths still needed for migration

### Conventions For Future Changes

- package lists should stay in role defaults
- hostnames, domains, and paths should stay in host vars
- static config files should go under `files/`
- comments should explain why a choice exists, not narrate every line

### Known Reality

- the old raspi still matters as migration knowledge, but should not dictate the
  final design
- public DNS and NAT still need deliberate validation before full production
  cutover
- `ansible-pull` may print a hostname-pattern warning during its internal git
  step; the actual playbook result matters more than that warning
