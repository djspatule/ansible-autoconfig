# Ansible Autoconfig

<!--toc:start-->

- [Ansible Autoconfig](#ansible-autoconfig)
  - [Usage](#usage)
  - [ToDo](#todo)
    - [Guidelines for coding agents](#guidelines-for-coding-agents)
      - [Objectives](#objectives)
      - [Roles](#roles)
      - [Extra instructions](#extra-instructions)
      - [Do not do](#do-not-do)
  - [Agent written readme](#agent-written-readme)
    - [Design Rules](#design-rules)
    - [Active Layout](#active-layout)
    - [Current Entry Points](#current-entry-points)
    - [Secrets And Vault](#secrets-and-vault)
    - [Linting](#linting)
    - [Testing On A VM](#testing-on-a-vm)
    - [Why `requirements.yml` Stays](#why-requirementsyml-stays)
    - [What `group_vars/all` Still Does](#what-group_varsall-still-does)
    - [Storage Model](#storage-model)
    - [Dotfiles Model](#dotfiles-model)
    - [Pi-hole Source Of Truth](#pi-hole-source-of-truth)
    - [Serverannah Notes](#serverannah-notes)
    - [Conventions For Future Changes](#conventions-for-future-changes)
    - [Known Reality](#known-reality)
    <!--toc:end-->

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

- [x] initiate base role
- [ ] implement server roles (fresh arch and ubuntu machines compatible)
  - [ ] keep server and workstation roles Arch-compatible where practical for
        server flexibility and future distro hopping
  - [x] use tags to only test/execute parts of the ansible-autoconfig script...
        that should accelerate dev/debug and limit need for protection against
        downloads (to preserve bandwidth).
  - [x] include running pi-hole update as part of the ansible playbook? Include
        also homepage update, etc. (since they are dockers, pull the latest
        image?)
  - [ ] pull latest container images on each run unless it slows runs down too
        much
- [ ] server services
  - [x] **nextcloud**: implement "old" users ?
  - [x] re-establish when possible the conf file for Homepage as on raspi (with
        the same "widgets" when relevant). Update also the links there.
  - [ ] **other services**:
    - [x] borg backups for
      - [x] server services
      - [ ] server files, including aumenuilya, tabletop-timer, and other
            service data
    - [ ] timeshift back-up on SSD_512 for simple system-level checkpoints and
          restore points for serverannah internal storage only
    - [ ] Odoo with small database stored on serverannah internal SSD under
          /home
    - [ ] Plex reading media from SSD_1TO
    - [ ] Dictation app/server (voxtype, whisper, etc.) ? Need to be discussed
          before.
    - [ ] Excalidraw docker (at draw.dinnizer.com, secured via caddy auth)
    - [ ] have docker-compose to try new dockers easily (Tryton, ERPNext, Hermes
          agent, Odysseus by PewDiePie, etc.)
- [x] **aumenuilya**:
  - [x] why is it an old version and not the one "running" on the pi ? use SSH
        to create the latest back-up and replace in SSD_1TO (keep the old
        back-up).
  - [x] updating wordpress to its latest version doesn't work....Debug.
- [ ] dinnizer
  - [ ] **App.dinnizer.com**:
    - [x] correct minimally and deploy the dinnizer app at app.dinnizer.com.
    - [ ] make the last debugs/improvements. These come from
          `Dinnizer app todo.csv` (kept as the detailed scratch list until the
          items below are closed; the relevant still-open ones are folded in
          here):
      - [ ] BUG: front UI breaks when a dinner has too many guests or recipes
      - [ ] BUG: `dinner_form`
      - [ ] order index pages with `.order(:last_name, :created_at)`
      - [ ] front: list each recipe's dinners and guests
      - [ ] add a Markdown content editor for recipe descriptions (if an easy
            gem exists)
      - [ ] seed the recipe base with aumenuilya recipes (or link to a recipe
            list)
      - [ ] save photos in the seed so `db:seed` does not drop them
      - [ ] link a recipe's ingredients to each guest's likes and dislikes
      - [ ] allow recipes to be categorized
      - [ ] generate default "initials" pictures for users, guests and recipes
      - [ ] add a per-user stats page
      - [ ] (later/marketing) usecase video, JBB feedback
  - [ ] develop a very simple dinnizer landing page at dinnizer.com for a CFO
        part time service.
    - [ ] serve it as a standalone static Caddy site
    - [ ] write it in HTML with the latest Material Design implementation
    - [ ] use this palette:
          <https://colorhunt.co/palette/f9f7f7dbe2ef3f72af112d4e>
    - [ ] define page contents later
- [ ] tabletop-timer
  - [ ] slightly upgrade the tabletop-timer app ? focus on mobile responsivness
        and upgrade the app's security and usability without changing the code
        significantly as it was and still needs to be the fruit of my work for
        the major part.
- [ ] analytics and monetization
  - [ ] **Google Analytics** :
    - [ ] configure tabletop-timer with G-5E4TWCP28D
    - [ ] configure app.dinnizer with G-SB091QKKGE
    - [x] leave aumenuilya alone because it was set up another way
    - [ ] add advertising/monetization to these three sites?
- [ ] secure server
  - [ ] implement tailscale
  - [x] implement caddy auth for homepage and bentopdf and fail2ban jail after
        several failed attemps.
- [x] update server automatically
  - [x] run ansible-pull on a schedule. Implemented in `roles/base` as a systemd
        timer (`autoconfig-pull.timer`, `OnCalendar=daily`,
        `RandomizedDelaySec=30m`, `Persistent=true`) plus a helper script and a
        oneshot service. Works on both Arch and Debian families.
  - [ ] optionally add a dedicated passwordless-sudo user. The timer currently
        runs as root via systemd, so this is now a hardening nicety, not a
        blocker.
- [ ] implement workstation role
  - [ ] dotfiles:
    - [x] create first CLI/TUI/dotfiles foundation
    - [x] migrate the first CLI/TUI dotfiles from the standalone
          `omarchy-dotfiles` repo into `files/dotfiles/`: `nvim`, `git`, `gh`
          config, plus the existing `bash`/`starship`/`tmux`/`ssh`/`opencode`.
          Validated on the VM.
    - [ ] keep migrating remaining CLI/TUI dotfiles as needed (GUI/Omarchy
          desktop config stays out of scope, see below)
    - [x] protect secrets with ansible-vault so nothing lands in this public
          repo unencrypted. `~/.ssh/config.local` is vault-encrypted and
          deployed by copy-decrypt; the `gh` OAuth token is deliberately not
          committed (see [Secrets And Vault](#secrets-and-vault)).
  - [x] test on the disposable Arch/Omarchy VM (`savannarchome`). Self-pull via
        `ansible-pull` validated: base + workstation, Stow dotfiles, and the
        vaulted `config.local` deploy all apply with `failed=0`. See
        [Testing On A VM](#testing-on-a-vm).
  - [x] vault-password-file plumbing is wired end to end (bootstrap script,
        ansible-pull timer, `ansible.cfg`) and proven on the VM.
  - [ ] workstation stays CLI/TUI only for now. GUI/Omarchy config is
        intentionally out of scope (the old Betterbird/Thunderbird automation
        was removed as stale).
- [ ] implement kids role
- [ ] find inspiration in
      [jaylacroix's code](https://github.com/LearnLinuxTV/personal_ansible_desktop_configs/tree/main)
      and eventually omakub's code or Jeff Geerling's code to improve the whole.

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

My dotfiles are currently specific to Omarchy and managed with stow
(<https://github.com/djspatule/omarchy-dotfiles>)... I want to transition from
the dotfiles specific repo to this repo and have stow managed by ansible as part
of the setup. Maintenance of the files need to be feasible and easy.

- Use this for inspiration of structuration, etc.
  <https://github.com/LearnLinuxTV/personal_ansible_desktop_configs/tree/main>
- I’m writing this code also as an opportunity to learn about ansible,
  GNU/linux, neovim, opencode and other coding agents (and vibecoding in
  general), tmux, git, networking, etc. Thus explain all the code, design
  choices, structure, etc in that perspective...
- I would ideally like to lay here the foundations of an auto-config ansible
  setup that will be still valid and usable in 20 years….(comment your code
  profusely in that regard)
- The short term priority is to work on the server but the rest will be
  addressed as well (kids computer, adult's workstations, etc.).

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
- `roles/workstation`: first CLI/TUI and dotfiles foundation for Arch/Omarchy
  workstation testing
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
sudo ansible-pull -U https://github.com/djspatule/ansible-autoconfig.git -C main -d /opt/ansible-pull local.yml
```

When testing on a VM or before public DNS/port forwarding is ready, do not ask
Caddy to obtain public HTTPS certificates yet. Keep the real `serverannah` vars
as the production target, and override only the staging network edge explicitly:

```bash
sudo ansible-pull -U https://github.com/djspatule/ansible-autoconfig.git -C main -d /opt/ansible-pull local.yml \
  -e 'server_reverse_proxy_auto_https=false server_reverse_proxy_published_ports=["8081:80"] server_reverse_proxy_sites=[{"hostname":"homepage.localtest.me","upstream":"homepage:3000"},{"hostname":"bentopdf.localtest.me","upstream":"bentopdf:8080"},{"hostname":"game-timer.localtest.me","upstream":"game-timer:80"},{"hostname":"pihole.localtest.me","upstream":"pihole:80"}]'
```

This keeps VM testing local and avoids confusing Let's Encrypt failures while
the server is not publicly reachable.

Bootstrap a fresh server that does not have Ansible yet:

```bash
sudo ./scripts/bootstrap-server.sh
```

Dry-run a local checkout when testing:

```bash
sudo ansible-playbook -i hosts --limit serverannah local.yml --check
```

### Secrets And Vault

This is a **public** repo, so secrets are handled at two levels:

1. **Generated on the host, never committed.** Service passwords (database
   passwords, Nextcloud admin password, Dinnizer secret key base, etc.) are
   generated on the target machine into `/etc/ansible/secrets/` on first run and
   reused afterwards. They never enter git at all. This is the default and
   covers most services today.
2. **Committed but encrypted with `ansible-vault`.** For files that genuinely
   have to live in the repo (for example SSH config or private keys, API tokens
   in dotfiles), encrypt them with `ansible-vault` before committing. The
   encrypted blob is safe in a public repo; only the password that unlocks it is
   secret.

The vault password itself is never committed. Supply it one of two ways:

```bash
# Per command:
sudo ansible-playbook -i hosts local.yml --vault-password-file ~/.ansible-vault-pass

# Or for every run: uncomment vault_password_file in ansible.cfg.
```

The same `--vault-password-file` flows through `scripts/bootstrap-server.sh`
(`AUTOCONFIG_VAULT_PASSWORD_FILE`) and the managed `autoconfig-pull` timer
(`autoconfig_vault_password_file`), so a scheduled pull can decrypt vaulted
files unattended. Password-file names like `~/.ansible-vault-pass`, `secret.txt`
and `*.vault-pass` are already in `.gitignore`.

Common commands:

```bash
ansible-vault encrypt files/dotfiles/ssh/.ssh/config   # encrypt in place
ansible-vault edit    files/dotfiles/ssh/.ssh/config   # edit encrypted
ansible-vault view    files/dotfiles/ssh/.ssh/config   # read without decrypting to disk
```

> Keep `vault_password_file` commented in `ansible.cfg` until at least one
> encrypted file exists, otherwise runs fail looking for a password they do not
> need.

### Linting

Linting is local-only. There is no GitHub Action and no cloud cost: everything
runs on your machine.

- `scripts/lint.sh` runs `yamllint` + `ansible-lint`. On first run it builds a
  throwaway virtualenv (`.lint-venv/`, gitignored) so nothing is installed
  system-wide. Run it any time:

  ```bash
  ./scripts/lint.sh
  ```

- A **pre-commit hook** is an optional convenience: a check that git runs
  automatically every time you `git commit`, refusing the commit if linting
  fails (so mistakes never reach history). It is configured in
  `.pre-commit-config.yaml` and is also fully local. One-time setup:

  ```bash
  pipx install pre-commit   # or: pip install --user pre-commit
  pre-commit install        # installs the hook into .git/hooks
  pre-commit run --all-files  # optional: lint everything now
  ```

Config lives in `.yamllint` (lenient: long lines warn, real booleans only) and
`.ansible-lint` (`basic` profile; the role-prefix naming rule is deliberately
skipped because this repo names variables by concern, e.g. `nextcloud_`,
`pihole_`, not `server_nextcloud_`). The remaining findings are cosmetic (long
lines, a few unnamed `import_tasks`) and can be cleaned up over time.

### Testing On A VM

The workstation role is proven on a disposable Arch/Omarchy VM (`savannarchome`)
before touching a real laptop. The VM configures **itself** with `ansible-pull`,
exactly like a real new machine would, so no host-to-guest SSH or
port-forwarding is needed.

GNOME Boxes uses QEMU user-mode networking (the guest gets `10.0.2.15`, which
the host cannot reach), so the self-pull model is not just convenient, it is the
only simple option. Three lines inside the VM:

```bash
# 1. ansible-pull targets the inventory host whose name matches the machine's
#    hostname, so the VM must call itself savannarchome.
sudo hostnamectl set-hostname savannarchome

# 2. The vault password (same one used on the laptop) so config.local can decrypt.
printf '%s' 'YOUR_VAULT_PASSWORD' > ~/secret.txt && chmod 600 ~/secret.txt

# 3. Fetch and run the bootstrap: installs git+ansible, clones, installs
#    collections, runs ansible-pull for base + workstation.
curl -fsSL https://raw.githubusercontent.com/djspatule/ansible-autoconfig/main/scripts/bootstrap-server.sh \
  | sudo env AUTOCONFIG_VAULT_PASSWORD_FILE=/home/lion/secret.txt sh
```

A healthy first run ends with `failed=0` and shows, among others, the
`Deploy vault-encrypted dotfiles (decrypted into place)` task as `changed` (a
wrong vault password would fail there). Reset or snapshot the VM freely between
runs; the playbook is idempotent.

**Live access from the host (for fast iteration):** the self-pull above is
enough to validate a change, but to drive `--check` runs against the VM from the
host (or just poke around), a reverse SSH tunnel avoids fighting GNOME Boxes'
NAT. GNOME Boxes user-mode networking reaches the host at `10.0.2.2`, so run
**one command in the guest** to dial out and forward host port 2222 back to the
guest's sshd, then **one on the host** to install your key through it:

```bash
# In the GUEST: hold open a reverse tunnel (host:2222 -> guest:22).
ssh -fN -R 2222:127.0.0.1:22 lion@10.0.2.2

# On the HOST: authorize your key over that tunnel.
ssh-copy-id -p 2222 lion@127.0.0.1
```

After that, `ssh -p 2222 lion@127.0.0.1` works, and because
`host_vars/savannarchome` already points at `127.0.0.1:2222`, so does
`ansible -i hosts savannarchome -m ping`. The tunnel lasts until the VM reboots
or that `ssh` process is killed; wrap it in `autossh` + a systemd user unit if
you want it to persist.

**Clipboard with GNOME Boxes (Hyprland guest):** install `spice-vdagent` and
`wl-clipboard`, enable `spice-vdagentd`, and add `exec-once = spice-vdagent`
(without `-x`) to the Hyprland config so the client starts inside the Wayland
session. Sync is then automatic (normal copy/paste, no special shortcut). If the
client comes up in X11 mode (`spice-vdagent -x`), it cannot read the Wayland
clipboard; `pkill -x spice-vdagent` then re-run `spice-vdagent` from a terminal
in the live session.

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

Storage was simplified on purpose, but Ansible does not replace the whole system
`/etc/fstab` anymore. The OS installer should keep owning `/`, `/boot`, EFI and
swap because their UUIDs are created during installation.

The repo ships only the data-disk entries:

- source: `files/serverannah/etc/fstab`
- deployed into: a marked Ansible block inside `/etc/fstab`

The server role then:

1. inserts or updates the marked data-mount block
2. creates the mount points declared in that source file
3. runs `mount -a`

This keeps data mounts versioned without hard-coding boot/root UUIDs that belong
to one specific installation.

### Dotfiles Model

Dotfiles are handled with:

- Ansible as orchestrator
- Stow as symlink engine for plaintext configs
- `ansible-vault` + a copy-decrypt step for the few configs that contain secrets

Plaintext packages live under `files/dotfiles/<package>/` mirroring the home
layout, and are listed per host in `dotfiles_stow_packages`. The migrated set is
`bash`, `starship`, `tmux`, `opencode`, `claude`, `nvim`, `git`, `gh`, and the
sanitized public `ssh` config. These are symlinked into `$HOME` by Stow.

Note two deliberate boundaries:

- `gh` ships only `config.yml`. `hosts.yml` holds a GitHub OAuth token and is
  **not** committed, even encrypted — let `gh auth login` recreate it per host.
- the `ssh` package ships only the sanitized public config, which does nothing
  but `Include ~/.ssh/config.local`. The real host aliases live in that local
  file.

Secret dotfiles (currently `~/.ssh/config.local`) are stored **vault-encrypted**
under `files/dotfiles-secret/` and listed in `dotfiles_secret_files`. They
cannot be Stow-symlinked, because the symlink would hand the application the
ciphertext; instead Ansible copies them into place and decrypts on the way (see
[Secrets And Vault](#secrets-and-vault)). To update one:

```bash
ansible-vault edit --vault-password-file ~/secret.txt files/dotfiles-secret/ssh/config.local
```

GUI/Omarchy desktop config (Hyprland, Waybar, etc.) is intentionally **not**
migrated yet: the workstation role stays CLI/TUI only for now.

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
