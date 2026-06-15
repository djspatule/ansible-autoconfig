# PLAN

Dependency-ordered. [P] = parallelizable, [S] = sequential/blocking.

## A — Repo pass (branch `repo-cleanup`)
- A.1 [S] Remove 6 empty role scaffolds. **[done]**
- A.2 [P] Stale-comment sweep across `roles/`, `README.md`, templates — fix only
      comments that misdescribe current behaviour. No logic changes.
- A.3 [P] Dead-code/value sweep (unused vars, leftover blocks).
- A.4 [S] Resolve or re-justify the single `TODO` in `roles/base/tasks/dotfiles.yml`
      (legacy bash/starship tasks). Conservative: keep them (git-history value),
      tighten the comment — do **not** do the risky collapse under "conservative".
- A.5 [S] Verify: yamllint, ansible-lint, syntax-check, `--check --diff` on
      savannarchome. Commit focused. Open for review / merge.

## B — Kids host (after recon)
Interface/contract per task:
- B.1 [S] **Recon** (read-only SSH): OS/version, hostname, DE, users + groups,
      `timekpr` config files (`/etc/timekpr/*`, per-user), installed apps
      (manual-install set via `apt-mark showmanual`). Output: a captured snapshot.
- B.2 [S] `local.yml` + base: make Linux Mint a first-class Debian-family distro
      (fix the apt/distribution gates). Contract: Mint runs base role cleanly.
- B.3 [S] `roles/kids/`: users (oscar, romy) → timekpr install + captured config
      → captured app list. Each sub-step idempotent and commented.
- B.4 [S] Inventory: add `[kids]` group + host, `host_vars/<name>`, a `kids` play
      in `local.yml`.
- B.5 [S] Verify with `--check` against the live host; confirm no daddy lockout.

## Notes on framework fit
- No `.claude/agents/` exist → no subagent dispatch; done inline.
- "Test harness" for an Ansible repo = lint + syntax-check + `--check` dry runs.
