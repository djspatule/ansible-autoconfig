# PROGRESS

Newest first.

## 2026-06-15
- Phase 0 intake complete; questions answered by user.
- Branch `repo-cleanup` created.
- A.1 done: removed 6 empty role scaffolds (server_autopull, server_base,
  server_bentopdf, server_homepage, server_reverse_proxy, server_stirling_pdf).
  They were untracked empty dirs → no git diff, just disk cleanup. Confirmed
  unreferenced (matches were variable-name prefixes, not role loads).
- State files created under `docs/orchestrator/`.
- BLOCKER (B): SSH to `daddy@192.168.1.41` has no key auth and no `sshpass`
  locally → asked user to run `ssh-copy-id -i ~/.ssh/id_ed25519_homelab.pub
  daddy@192.168.1.41`. Recon resumes once the key is installed.
- Noted for B: `local.yml` apt gates exclude "Linux Mint"; base uses os_family
  (Debian) so packages work, but cache-update/upgrade/cleanup tasks skip on Mint.
- A.5 lint: `./scripts/lint.sh` found 28 `braces` ERRORS in nextcloud.yml (my own
  Redis/SMTP flow-mapping loops, already on main). Fixed by stripping inner-brace
  padding → **0 errors** now. 30 line-length warnings remain (pre-existing,
  documented as acceptable). syntax-check passes.
- A.2 partial: README "Dotfiles Model" hard-coded a stale "migrated set" list →
  replaced with a pointer to `dotfiles_stow_packages` (won't go stale again).

## 2026-06-15 (cont.) — Workstream B
- SSH key installed by user; recon done. Host = `kidsbook`, Linux Mint 22.3
  (Zena) XFCE, x86_64, python3.12. Users daddy(1000,sudo)/oscar(1001)/romy(1002);
  custom groups parent(2001), gamers(2002). timekpr-next 0.5.4 enabled+active.
- Captured timekpr policy verbatim into `files/kids/timekpr/` (main + 3 user
  confs). Policy: oscar/romy 15 min weekdays / 30 min weekends, allowed 16-20h
  school days; daddy unrestricted; lockout=terminate.
- Built `roles/kids/` (users/groups, timekpr install+config, apps) + handler.
- Curated kids apps from `apt-mark showmanual` (which is the whole OS): apt
  learning (gcompris-qt, tuxmath/paint/type, stellarium), apt games (supertux(kart),
  frogatto, abe, crawl-tiles, mrrescue, numptyphysics, sopwith, thingy), steam,
  gamemode, + Flathub set (Endless games, Scratch, Luanti, GNOME Chess, etc.).
- Wired inventory `[kids]` + `host_vars/kidsbook` + kids play in local.yml.
- Fixed B6: local.yml apt gates now use `os_family == "Debian"` (Mint covered).
- Verified: syntax-check OK, 0 lint errors, ansible reaches kidsbook key-based.

## OPEN / needs user
- Confirm/trim the curated app list (the one real judgment call — which packages
  are "the kids setup" vs Mint defaults). Touché flatpak excluded as a system util.
- A real `--check` (then live) run on kidsbook is pending: needs become pass at
  run time; not done from here. timekpr file-deploy vs daemon-rewrite to watch.

## Budget
- Within normal limits. No thrashing.
