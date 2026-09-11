# PROGRESS — autonomous trading agent

## Status: WAVE 1 COMPLETE — safety layer built and green

Branch `feat/trading-agent`. 27/27 tests passing, wired into `scripts/lint.sh`
so the pre-commit hook gates them alongside the Ansible linting.

### Done
- **Phase 0** intake: BRIEF, ACCEPTANCE (33 items), DECISIONS (10 assumptions,
  5 operator overrides, 2 accepted risks).
- **Phase 1** PLAN.md: module contracts written before code; deployment layout
  decided (source rides the existing ansible-pull checkout, mutable state lives
  outside it because the pull runs `git clean -fd`).
- **Phase 2** 27 failing acceptance tests, then made to pass.
- **T0.3** `.claude/agents/` — three specialists written, since the directory
  the protocol referenced did not exist.
- **T1.1 config.py** — two-signal live gate (E1-E3 green).
- **T1.2 state.py** — SQLite, kill switch and approvals survive restart (B1, C2).
- **T1.3 guardrails.py** — A1-A7 green, including NaN and latched breaker.
- **T2.1 broker.py** — A6 structural isolation green, idempotency key stable.

### Verified by the orchestrator, not claimed
Every test above was re-run here after implementation. `pytest tests/ -q` → 27
passed. Structural tests (A6, E3) grep the source tree, so they keep holding as
the code grows rather than only at the moment they were written.

### Not started
Wave 2 (universe, telegram, kill-switch-under-load), Wave 3 (catalysts,
reasoning, LangGraph, reconciliation), Wave 4 (Ansible role, deploy), Wave 5.

### Blockers
None. Waves 2-3 need credentials only for their `network`-marked tests, which
are excluded from the default run.

### Budget
Comfortable. No compaction risk; state is on disk and committed after each step.
