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

## OPEN — see QUESTIONS in the Phase 0 output
Language choice (Python vs Rust), the meaning of "pauto", risk parameters, the
instrument universe, and the missing credentials.
