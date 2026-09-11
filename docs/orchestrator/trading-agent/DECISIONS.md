# DECISIONS — autonomous trading agent

## ASSUMED (defaulted; say the word and any of these changes)

- **A-01 Lives in this repo** as `roles/trading_agent/`, not a separate repo.
  Follows the amendment that this repo's conventions win, and means a rebuilt Pi
  restores the agent automatically.
- **A-02 Secrets are vault-encrypted in the repo**, not hand-placed on the Pi.
  A vault password now exists at `~/secret.txt` on raspi, so a nightly
  `ansible-pull` can decrypt. This beats host-only files on the one axis that
  matters here: a rebuilt SD card restores the keys with no manual step, which
  host-only files cannot.
- **A-03 The `.env` is rendered by Ansible** from vaulted values, not
  hand-edited. The brief asked for a gitignored `.env`; the file still exists
  and is still gitignored, but it is generated, so it survives a rebuild.
- **A-04 SQLite, not JSON**, for state. Concurrent reads from the Telegram
  handler and the reasoning loop, plus the need for atomic writes around order
  submission, are exactly what a JSON file handles badly.
- **A-05 Reasoning loop is event-driven**, triggered by a schedule during market
  hours and by incoming Telegram messages — not a tight poll. Cheaper in tokens
  and easier to reason about.
- **A-06 One systemd unit**, not separate agent/bot services. Two processes
  sharing SQLite state and a kill switch is a distributed-systems problem this
  project does not need.
- **A-07 Client-side idempotency key** on every order so a crash between
  "decided" and "submitted" cannot double-fill on restart (D2).
- **A-08 US equities only** for v1, regular hours, no options/crypto/shorting.
  Narrower blast radius while the guardrails are still unproven.
- **A-09 Approval timeout = DENY.** An unanswered approval must never become an
  approval. Timeout value goes in config.
- **A-10 Unattended nightly upgrades stay ON.** Operator decision, made
  knowingly. Accepted risk, recorded rather than silently inherited: a nightly
  `apt upgrade dist` can restart services or replace the Python under a venv
  mid-session. Mitigations that follow from it: the venv pins its own
  interpreter, the unit restarts on failure, and `OnFailure=` alerts.

## ACCEPTED RISKS
- **R-01** Nightly unattended upgrades on a machine running a financial process
  (see A-10). Operator-accepted; amount at risk is small.
- **R-02** The Alpaca paper keys were pasted into a chat transcript. Paper only,
  so the exposure is limited to a simulated account, but they should still be
  rotated before real use. See QUESTIONS.

## OPERATOR OVERRIDES (round 2) — decisions that changed the design

- **O-01 No mandatory human approval.** The original brief listed
  human-in-the-loop as non-negotiable; the operator has deliberately reversed
  that, wanting to see what the agent does autonomously with a small, isolated,
  written-off amount. Recorded as a reversal rather than quietly dropped,
  because it removes one of the two brakes the brief was built around.

  Consequence, stated plainly: **the deterministic guardrails become the ONLY
  thing standing between the agent and the account.** Every acceptance item in
  section A gets stricter as a result, not looser.

  Implementation: the approval code path is still built, with the threshold
  defaulting to "never ask". Re-enabling it is then a config change rather than
  a rewrite — which matters the first time something surprising happens.
  The agent may still *ask for an opinion*; it just does not *block* on one.

- **O-02 Reasoning runs through opencode on serverannah** (option (a)), so the
  provider can be swapped without touching this code.

  Consequence: the Pi now depends on another host being up. For a process that
  can hold positions, that is a real failure mode, so it is handled explicitly —
  losing opencode must mean **stop opening new positions**, never retry blindly
  or guess. The guardrails and kill switch are deliberately LLM-free and keep
  working when serverannah does not.

- **O-03 Account: $1000 to start**, cap configurable.
- **O-04 Instrument selection by exchange + sector filter**, not a hand-kept
  list. See QUESTIONS: Alpaca's asset API does not carry a usable sector field,
  so the filter needs a concrete data source before it can be enforced
  deterministically.
- **O-05 News from Alpaca**, included with the existing keys.

## OPEN — see QUESTIONS in the Phase 0 output
Language choice (Python vs Rust), the meaning of "pauto", risk parameters, the
instrument universe, and the missing credentials.
