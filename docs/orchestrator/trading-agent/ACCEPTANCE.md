# ACCEPTANCE — autonomous trading agent

Every item is checkable by a command or a test. Nothing here is satisfied by
inspection or by an agent reporting success. Items marked **[BLOCKED]** cannot be
verified until the corresponding credential or decision arrives.

## A. Guardrails — the deterministic brakes
The whole system's safety rests here, so these are tested in isolation, with no
network and no LLM.

- [ ] A1 Order exceeding max position size is REJECTED. Unit test, no network.
- [ ] A2 Order pushing total deployed capital over the cap is REJECTED.
- [ ] A3 Order number N+1 on a day capped at N is REJECTED.
- [ ] A4 Once realised+unrealised daily loss crosses the cutoff, every
      subsequent order is REJECTED until the next trading day.
- [ ] A5 While kill-switch state is STOPPED, every order is REJECTED.
- [ ] A6 Guardrail rejection is impossible to bypass: a static check proves the
      Alpaca order-submitting call appears in exactly one module, and that
      module is reachable only through the guardrail entry point.
      Verified by test, not by convention.
- [ ] A7 Guardrail decisions depend on no LLM output and no network: the test
      suite for A1-A5 passes with network disabled.

## B. Kill switch
- [ ] B1 `/stop` sets state to STOPPED within 5s and the state survives a
      process restart (persisted, not in-memory).
- [ ] B2 `/stop` attempts to cancel open orders and logs the outcome per order.
- [ ] B3 `/resume` is the ONLY thing that clears STOPPED. No timeout, no
      automatic recovery, no LLM path to it.
- [ ] B4 `/stop` works when the reasoning loop is wedged — proven by a test that
      blocks the reasoning task and still observes the state change.

## C. Human-in-the-loop
- [ ] C1 A trade classified "important" is NOT sent to Alpaca before an explicit
      Telegram approval.
- [ ] C2 A pending approval survives a process restart (persisted).
- [ ] C3 A pending approval expires safely: on timeout it is DENIED, never
      auto-approved.
- [ ] C4 The importance threshold is config, changeable without code edits.

## D. Crash safety
- [ ] D1 On startup, local state is reconciled against Alpaca's actual account;
      any divergence is logged and Alpaca is treated as truth.
- [ ] D2 Restarting mid-flight produces no duplicate order — proven by a test
      that kills the process between "decided" and "submitted", using a
      client-side idempotency key.
- [ ] D3 systemd unit restarts on failure and starts on boot; verified with
      `systemctl is-enabled` and an induced crash.

## E. Paper-trading safety
- [ ] E1 Default config points at Alpaca's PAPER endpoint. Asserted by test.
- [ ] E2 Live trading requires a config change AND a separate confirmation; a
      test proves live cannot be reached by config alone.
- [ ] E3 A test fails if the live endpoint appears anywhere reachable by default.

## F. Audit log
- [ ] F1 Every decision, tool call, order and reasoning trace is written with a
      timestamp and a correlation id linking them.
- [ ] F2 Given an order id, a command reconstructs the full chain that led to
      it. Verified end to end on a real paper order.
- [ ] F3 Logs rotate with a size cap; a test proves the cap holds (the Pi has a
      finite SD card and this runs continuously).

## G. Ansible / repo integration
- [ ] G1 The agent is deployed by a role in this repo, not installed by hand.
- [ ] G2 `ansible-pull` on raspi is idempotent: a second consecutive run reports
      0 changed for the agent's tasks.
- [ ] G3 No secret appears in the repo in plaintext — grep-based test over the
      working tree AND the git history.
- [ ] G4 `scripts/lint.sh` passes (yamllint, ansible-lint, rendered-shell).
- [ ] G5 The unit has `OnFailure=` wired to the notifier, and a deliberate
      failure produces an ntfy alert. Verified by inducing one.
- [ ] G6 Secrets reach the Pi reproducibly: a rebuild restores them without
      manual re-entry.

## H. Operation
- [ ] H1 The agent does not attempt to trade when the market is closed.
- [ ] H2 **[BLOCKED]** A paper order placed by the full pipeline appears in
      Alpaca. Needs working credentials.
- [ ] H3 **[BLOCKED]** "What did you do today and why" answerable over Telegram.
      Needs bot token + chat id.
