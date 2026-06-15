# ACCEPTANCE

Each item must be checkable by a command.

## A — Repo pass
- [ ] A1 `yamllint .` clean (or only documented, intentional warnings).
- [ ] A2 `ansible-lint` clean (or only documented warnings).
- [ ] A3 `ansible-playbook --syntax-check -i hosts local.yml` passes.
- [ ] A4 `roles/` contains only roles with real content that a play loads
      (`base`, `server`, `workstation`) — no empty scaffolds. [done]
- [ ] A5 `--check --diff` on `savannarchome` shows no behaviour change vs `main`.
- [ ] A6 Each logical change is its own focused commit.

## B — Kids host
- [ ] B1 Host added to inventory with `host_vars/<name>`; playbook runs green on
      it over SSH **without locking out `daddy`**.
- [ ] B2 `roles/kids/` exists, Mint/Debian-compatible, profusely commented.
- [ ] B3 `oscar` and `romy` accounts are managed idempotently (presence/groups,
      not passwords).
- [ ] B4 timekpr-next is installed and the **captured current** config is
      deployed; `timekpra --status <user>` (or config diff) matches the live box.
- [ ] B5 The currently-installed learning/gaming apps are captured into a
      package list and install idempotently.
- [ ] B6 Linux Mint is handled by the apt/distribution gates in `local.yml`
      (currently they skip "Linux Mint").
- [ ] B7 `--check` on the kids host shows convergence (no surprise changes).
