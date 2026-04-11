# Sprint Status

## Sprint Goal

Move the project from a mixed desktop/server experiment toward a real, idempotent
`ansible-pull` server platform centered on `serverannah`, while keeping the repo
 understandable and closer to the LearnLinuxTV structure.

## Scope Covered

This sprint focused on:

- server-first architecture
- convergent `ansible-pull` on `serverannah`
- migration of core raspi responsibilities where safe
- documentation of the repo and migration state
- groundwork for future dotfiles unification

## Completed

### Architecture

- Refactored the repo to a clearer LearnLinuxTV-style shape:
  - `local.yml` runs `base` on `all`
  - `server` runs only on `server`
- Parked workstation hosts out of active inventory for now to avoid dragging an
  unfinished desktop path into the server work.
- Split common vs server-only concerns:
  - `roles/base` now owns common packages, Stow-based dotfiles, and recurring
    `ansible-pull`
  - `roles/server` now owns storage, Docker, and server services

### Idempotent Self-Management

- `ansible-pull` works on `serverannah`
- recurring `systemd` timer is installed and enabled
- the current branch state converges on `serverannah` with `changed=0`

### Storage

- Backed up `serverannah`'s `fstab`
- turned the mount layout into structured host vars (`server_storage_mounts`)
- implemented mount management with `ansible.posix.mount`

### Dotfiles / Stow

- implemented the first Stow-based dotfiles path
- clones public `omarchy-dotfiles`
- stows selected packages into the target user's home
- currently manages:
  - `bash`
  - `starship`
- added handover logic for pre-existing unmanaged files/symlinks so first-run
  adoption is safe

### Common Base CLI

- common packages are installed cross-distro from `roles/base`
- added `starship`
- added `sqlite3`/`sqlite` because Pi-hole policy import needs it

### Core Services on `serverannah`

- Homepage
- BentoPDF
- vendored `game-timer`
- Nextcloud skeleton/service on `/mnt/SSD_1TO/nextcloud`
- AuMenuIlYA WordPress restore and deployment
- Caddy reverse proxy
- `fail2ban` with an active `sshd` jail

### Pi-hole

- captured enough Pi-hole state from the raspi to automate the current live
  policy model
- implemented staged Pi-hole on `serverannah` without touching household DNS
  yet:
  - DNS on `5300`
  - admin UI on `8089`
- verified:
  - Pi-hole admin UI responds
  - DNS queries to `192.168.1.7:5300` succeed
  - `systemd-resolved` remains active on the host
- imported the useful Pi-hole policy subset:
  - 28 enabled adlists
  - 197 exact allowlist entries
- made that import idempotent using a policy hash file

### Raspi Discovery / Migration Knowledge

Captured and documented real information from the raspi rather than cloning it
blindly:

- Homepage layout
- Nextcloud compose shape
- Nginx / NPM role in the old stack
- Frigate presence
- Pi-hole live behavior and policy data

### Documentation

- `guidelines.md`
- `ARCHITECTURE.md`
- `DOTFILES_PLAN.md`
- `backups/raspi/PIHOLE_AUDIT.md`

## Not Yet Completed

### Public Cutover

The Ansible side is in much better shape than the public internet side.

Still pending:

- final DNS cutover to `serverannah`
- router/NAT cutover for public HTTP/HTTPS if still pointing at the raspi
- final public certificate issuance through Caddy after DNS/ingress is correct

### Pi-hole Production Replacement

Pi-hole is now testable and much closer to cutover, but household DNS is not yet
pointed at `serverannah`.

Remaining step:

- move staged Pi-hole from `5300` to real `53` when you are satisfied with the
  test
- only then point the Freebox/clients to `serverannah`

### Desktop / Workstation Path

- workstation hosts are parked out of inventory
- old workstation-oriented task files still exist, but they are not the active
  focus
- the repo is now structurally cleaner, but the desktop side is intentionally
  paused

### Dinnizer

- Dinnizer was investigated and then parked
- it is a legacy Rails app and not a “simple next website”
- decision: stop short on app archaeology and prioritize infrastructure work

## Important Decisions Made

### Caddy over old raspi web stack

- The raspi was not actively using Caddy as its main reverse proxy
- `serverannah` is now moving toward a cleaner Caddy-based target architecture
  instead of reproducing the old host-nginx path exactly

### File-Managed Infra over GUI Control Planes

- kept Ansible + file-managed configs as the source of truth
- did not introduce ONCE or Nginx Proxy Manager as the main platform
- deferred tools like Portainer/Semaphore unless they clearly add value later

### Server-First Learning Path

- preferred small, proven slices over “migrate everything at once”
- used VM testing when useful, then validated on `serverannah`

## Known Risks / Caveats

- `ansible.posix.mount` emits a deprecation warning from the collection/module
  implementation; this is noisy but not currently a functional problem in our
  code
- public websites are not “done” until DNS/NAT are aligned with `serverannah`
- Pi-hole production cutover still needs a final deliberate switch, even though
  the staged test is now solid
- Nextcloud is deployed, but should still be validated from a browser and then
  hardened further

## Recommended Next Sprint Backlog

### Highest Priority

1. Finish external cutover
   - verify DNS A records
   - verify NAT to `serverannah`
   - let Caddy complete TLS cleanly

2. Decide Pi-hole go-live
   - keep staged test a bit longer or move to real `53`
   - only then update Freebox / clients

3. Harden Nextcloud
   - external validation
   - maintenance / backup strategy
   - possible cache layer later if needed

### Service Backlog from README + raspi reality

1. Frigate
   - high relevance because a camera is already on `serverannah`
   - also clearly existed on the raspi and is part of the real target stack

2. n8n
   - good next Docker service candidate
   - isolated enough to automate cleanly
   - should come after secrets/access decisions are a bit cleaner

3. Odoo
   - only after deciding exact scope and edition expectations

4. Backup strategy for the server itself
   - now more urgent because multiple persistent services exist on
     `/mnt/SSD_1TO`

## Analysis of New Short Todo List

### 1. Sécuriser les accès (Tailscale? Infisical, Caddy?)

Recommendation:

- `fail2ban` was the right first move and is now done
- `Tailscale` is the next most practical security improvement
- `Infisical` is useful later, but probably not the next move
- `Caddy` is already part of the exposure path; it helps with TLS and reverse
  proxying, but it is not the main answer to admin-access security

Priority suggestion:

1. `Tailscale`
2. SSH hardening / access review
3. secret-management improvements (`Infisical` only if the secret sprawl grows
   enough to justify another control plane)

Why:

- Tailscale gives immediate practical admin value without rewriting the current
  stack
- Infisical is powerful, but right now the repo already uses target-side secret
  files and some Ansible-safe patterns; adding Infisical too early may create
  more platform complexity than benefit

### 2. Docker Odoo

Question: is accounting free in self-hosted Community edition?

Pragmatic answer:

- do **not** assume Odoo Community is enough for the accounting scope you mean
- Odoo's editions/pricing/documentation presentation strongly suggests finance
  capabilities are one of the main Enterprise differentiators
- if your goal is serious accounting/compta rather than light invoicing, treat
  this as a product/edition decision first, not just a Docker deployment task

Recommendation:

- run a short spike before automating Odoo
- define exactly what “compta” means for you:
  - invoicing only?
  - bookkeeping?
  - French accounting localization/compliance?
- only then decide whether Odoo Community is a fit

Current priority: medium-low

### 3. Docker n8n

Recommendation: good candidate for a next service.

Why:

- self-contained
- popular and well-documented for Docker
- useful for household/workflow automation
- easier than Odoo from an application-risk perspective

Current priority: high-medium

Main prerequisite:

- cleaner secret handling for API tokens / credentials

### 4. Docker Ansible Semaphore

Question: is it pertinent?

Recommendation: not yet.

Why:

- the chosen model is `ansible-pull`
- Semaphore introduces another control plane, UI, DB, credentials, and execution
  model
- that is useful for teams, RBAC, on-demand runs, and centralized operations
  later, but not necessary to make this homelab reliable now

Verdict:

- useful later if you want UI-driven runs and task history
- not a near-term priority

Current priority: low

### 5. Syncthing for Obsidian vault replacing Notion

Recommendation: promising, but it solves a different problem than Notion.

Why:

- `Syncthing` is excellent for syncing an Obsidian vault privately across devices
- it is not a true Notion replacement for databases, sharing model, or structured
  collaborative workflows
- but if your real use case is “my notes and markdown vault everywhere”, it is a
  strong fit

Verdict:

- good candidate if the actual goal is private note sync
- not a full Notion replacement if you depend on Notion databases / collaboration

Current priority: medium

### 6. Setup Timeshift or Duplicati

These do not solve the same problem.

`Timeshift`:

- system rollback / system snapshots
- good for desktops
- not sufficient for service data protection on a Docker-heavy server
- the official project itself says it is for system files/settings, not user data

`Duplicati`:

- backup tool for data and remote targets
- closer to what a service-heavy server actually needs

Recommendation:

- for `serverannah`, favor a real data-backup approach over Timeshift alone
- Timeshift can still make sense on desktops or maybe for host-OS recovery, but
  not as the main backup answer for this homelab server
- if evaluating Duplicati, do a trust/maintenance check first; the current
  public marketing site looks unusual enough that I would verify project health
  and docs before committing to it

Current priority: high-medium

## Suggested Priority Order Right Now

1. Public DNS / NAT cutover validation
2. Decide Pi-hole go-live on real `53`
3. Tailscale
4. Backup strategy for server data
5. Frigate
6. n8n
7. Syncthing / Obsidian
8. Odoo spike
9. Semaphore only if the operating model changes

## Definition of Done for This Sprint

Achieved:

- `serverannah` is no longer just a target idea; it is actively configured by
  `ansible-pull`
- the repo now has a coherent `base` + `server` architecture
- key services are actually deployed
- a staged Pi-hole path exists and is testable without risking the household DNS
- `fail2ban` is in place before wider exposure

Not yet achieved:

- full public cutover from raspi to `serverannah`
- full retirement of the raspi
- desktop/workstation refactor
- full backup strategy for the new server state
