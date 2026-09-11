"""Operator commands.

Deliberately separate from the Telegram transport and from the reasoning loop.
The kill switch has to work when the agent is misbehaving, so the code path
from "operator typed /stop" to "state is halted" touches nothing that the
reasoning loop can block: no shared lock, no queue, no model call. It writes to
SQLite and returns.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    text: str
    changed: bool = False


def handle_command(text: str, *, state) -> CommandResult:
    cmd = (text or "").strip().split()[0].lower() if (text or "").strip() else ""

    if cmd == "/stop":
        state.set_kill_switch(True)
        return CommandResult(
            "HALTED. No new orders will be placed. Send /resume to restart.",
            changed=True,
        )

    if cmd == "/resume":
        # The only thing that clears it. No timeout, no automatic recovery, and
        # no path from the model — if the agent could resume itself the switch
        # would be advisory.
        state.set_kill_switch(False)
        return CommandResult("Resumed. Trading re-enabled.", changed=True)

    if cmd == "/status":
        halted = state.kill_switch_engaged()
        return CommandResult(
            f"{'HALTED' if halted else 'running'} | "
            f"deployed ${state.deployed_usd():.2f} | "
            f"{len(state.pending_approvals())} pending"
        )

    if cmd == "/help":
        return CommandResult("/stop  /resume  /status  /help")

    # Anything else is conversation for the agent, not a command. Notably it
    # must NOT clear a halt: a chatty message is not consent to resume.
    return CommandResult("")
