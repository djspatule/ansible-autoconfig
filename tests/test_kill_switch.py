"""ACCEPTANCE B1-B4 — the kill switch must work when nothing else does.

B4 is the interesting one: /stop has to take effect while the reasoning loop is
wedged. That is an architectural claim, not a behavioural one — it holds because
the switch lives in SQLite rather than in the loop's memory, so a blocked
thread cannot prevent the write or hide it from the next guardrail check.
"""
from __future__ import annotations

import datetime as dt
import threading
import time

from trading_agent.commands import handle_command
from trading_agent.config import Config
from trading_agent.guardrails import OrderIntent, evaluate
from trading_agent.state import State

NOW = dt.datetime(2026, 9, 11, 15, 0, tzinfo=dt.timezone.utc)


def test_b1_stop_engages_and_blocks_orders(tmp_path):
    s = State(tmp_path / "s.db")
    cfg = Config.for_testing()
    assert evaluate(OrderIntent("XBI", "buy", 10.0), state=s, config=cfg, now=NOW).allowed

    handle_command("/stop", state=s)
    assert s.kill_switch_engaged()
    d = evaluate(OrderIntent("XBI", "buy", 10.0), state=s, config=cfg, now=NOW)
    assert not d.allowed and "kill_switch" in d.reason


def test_b3_only_resume_clears_it(tmp_path):
    s = State(tmp_path / "s.db")
    handle_command("/stop", state=s)
    for noop in ("/status", "hello", "/help", "resume"):
        handle_command(noop, state=s)
        assert s.kill_switch_engaged(), f"{noop!r} must not clear the kill switch"
    handle_command("/resume", state=s)
    assert not s.kill_switch_engaged()


def test_b4_stop_works_while_the_reasoning_loop_is_wedged(tmp_path):
    """The whole point: a hung loop must not be able to hold the switch shut."""
    s = State(tmp_path / "s.db")
    cfg = Config.for_testing()
    wedged = threading.Event()
    released = threading.Event()

    def reasoning_loop():
        wedged.set()
        released.wait(timeout=5)  # stands in for a hung model call

    t = threading.Thread(target=reasoning_loop, daemon=True)
    t.start()
    assert wedged.wait(timeout=2), "loop did not start"

    start = time.monotonic()
    handle_command("/stop", state=s)
    elapsed = time.monotonic() - start

    assert s.kill_switch_engaged(), "stop must take effect with the loop wedged"
    assert elapsed < 5.0, f"stop blocked on the wedged loop ({elapsed:.1f}s)"
    assert not evaluate(
        OrderIntent("XBI", "buy", 10.0), state=s, config=cfg, now=NOW
    ).allowed
    released.set()


def test_b1_state_is_on_disk_not_in_memory(tmp_path):
    """The architectural reason B4 holds — a fresh handle sees the same flag."""
    path = tmp_path / "s.db"
    handle_command("/stop", state=State(path))
    assert State(path).kill_switch_engaged()
