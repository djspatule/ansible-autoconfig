# PROGRESS — autonomous trading agent

## Status: waves 1-4 largely built. 62/62 tests green.

Branch `feat/trading-agent`, pushed. Tests run inside `scripts/lint.sh`, so the
pre-commit hook gates them with the Ansible linting.

### Complete
| Task | Module | Acceptance |
|---|---|---|
| T1.1 | `config.py` — two-signal live gate | E1-E3 |
| T1.2 | `state.py` — SQLite, survives restart | B1, C2 |
| T1.3 | `guardrails.py` — the deterministic layer | A1-A7 |
| T1.4 | `audit.py` — correlation ids, rotation, redaction | F1-F3 |
| T2.1 | `broker.py` — sole Alpaca path, idempotency | A6, D1-D2 |
| T2.2 | `universe.py` — ETF-derived, offline seed | — |
| T2.3 | `commands.py` — /stop /resume /status | B1-B4 |
| T3.1 | `catalysts.py` — ClinicalTrials.gov + news | — |
| T3.2 | `reasoning.py` — opencode, fail-closed | O-02 |
| —    | `market.py` — regular hours only | H1 |
| T4.1 | `roles/trading_agent/` — venv, env, unit | G1 |

### Verified here, not taken on trust
Every figure above was re-run by the orchestrator after implementation:
`pytest tests/ -q` -> 62 passed. Two tests are structural rather than
behavioural (only `broker.py` imports Alpaca; only `config.py` names the live
endpoint) and grep the tree, so they keep holding as the code grows.

### Remaining
- `telegram_bot.py` — transport. `commands.py` already holds the logic and is
  tested independently of it, which is what makes B4 hold.
- `agent.py` — the LangGraph loop tying catalysts -> reasoning -> guardrail ->
  broker.
- `main.py` — entrypoint: reconcile, then loop.
- Wave 4 deploy to raspi and the live paper-account check (H2).
- Wave 5 ACCEPTANCE walk.

### Blockers
`OPENCODE_URL` is unset — needed before the loop can reason. Everything else is
credential-free and done.

### Budget
Comfortable. State flushed to disk and committed after each step.
