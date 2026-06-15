# BRIEF

Two workstreams requested 2026-06-15.

## A — Repo quality pass (conservative, behaviour-preserving)
Fix stale/misleading comments, remove dead code, tidy architecture **without
changing what the playbook does** to any machine. Verified by lint +
syntax-check + a `--check` dry run with no unintended diffs. Work on a
`repo-cleanup` branch for review before merge to `main` (prod pulls `main`).

## B — Kids machine "ansible-ready"
Bring the kids' computer under this repo as a managed host. **Do not invent**
parental controls or apps — **capture the machine's current setup** (timekpr-next
config, installed apps, existing accounts) and reproduce it idempotently in a new
`roles/kids/` role.

### Known facts
- Host: `daddy@192.168.1.41`, Linux Mint (XFCE; Cinnamon switch envisaged) on an
  old MacBook. Goals: gaming + learning. Parental control is strict and **already
  configured** with timekpr-next.
- Accounts already exist, one per kid: `oscar` (9) and `romy` (8). The role
  manages the accounts but **not** their passwords (no secrets in this public repo).
- DNS filtering is already handled network-wide by Pi-hole — nothing per-host.
- `daddy` stays the sole sudo/admin account.
