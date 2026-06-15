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

## Budget
- Within normal limits. No thrashing.
