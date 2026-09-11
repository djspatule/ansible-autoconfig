# BRIEF — autonomous trading agent on raspi

Namespaced under `trading-agent/` because `docs/orchestrator/` already holds the
completed June 2026 repo-quality workstream. That one is finished; this is not
a continuation of it.

## Goal, restated

Run a continuously-operating trading agent on the Raspberry Pi 4B (`raspi`,
192.168.1.99, Debian 13 trixie, aarch64, 3.7 GiB RAM). An LLM does the
reasoning; Alpaca executes; Telegram is the human interface. It trades **paper
money only** until explicitly changed.

The part that actually matters: this is a system that can lose money while
nobody is watching. So the real deliverable is not "an agent that trades" — it
is **a set of deterministic brakes that hold regardless of what the LLM decides,
plus an audit trail good enough to reconstruct any decision after the fact.**
The agent is the easy half.

## Amendments to the original brief (from follow-up messages)

1. **This repo's conventions win** over the brief's where they conflict. So:
   Ansible-managed, secrets follow the established model, systemd unit deployed
   by a role, `scripts/lint.sh` must pass, pre-commit hook gates every commit.
2. **Unattended nightly upgrades stay enabled** on raspi. Operator decision,
   made knowingly: the machine handles small amounts only. Logged in DECISIONS
   as an accepted risk, not as something overlooked.
3. **Failure notifications on**, with raspi generating its own ntfy topic
   separate from serverannah's.
4. A vault password now exists at `~/secret.txt` on raspi, so vault-encrypted
   secrets in the repo can decrypt during a nightly `ansible-pull`.

## Provided so far

- Alpaca **paper** endpoint + key + secret (received in chat; see QUESTIONS —
  they need rotating and storing properly before use).

## Not yet provided

Anthropic API key; Telegram bot token and chat ID; risk parameters; the
instrument universe. These block phases 1, 2 and 4 respectively.
