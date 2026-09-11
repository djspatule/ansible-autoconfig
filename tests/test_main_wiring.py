"""Entrypoint wiring — the threading guarantee behind the kill switch."""
from __future__ import annotations

import threading

from trading_agent.commands import handle_command
from trading_agent.state import State


def test_a_state_handle_cannot_be_shared_across_threads(tmp_path):
    """The constraint the two-loop design exists to respect. sqlite3 refuses a
    connection used from another thread, so each loop opens its own."""
    s = State(tmp_path / "s.db")
    errors = []

    def use_it():
        try:
            s.kill_switch_engaged()
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    t = threading.Thread(target=use_it)
    t.start()
    t.join()
    assert errors, "expected sqlite3 to refuse a cross-thread connection"


def test_separate_handles_on_one_file_see_each_others_writes(tmp_path):
    """Why the kill switch works: the command loop halts trading through its
    own handle while the work loop is stuck in a call it cannot interrupt."""
    path = tmp_path / "s.db"
    work_handle = State(path)
    assert not work_handle.kill_switch_engaged()

    wedged = threading.Event()
    released = threading.Event()

    def work_loop():
        State(path)  # its own handle, as in main.py
        wedged.set()
        released.wait(timeout=5)

    t = threading.Thread(target=work_loop, daemon=True)
    t.start()
    assert wedged.wait(timeout=2)

    # The command loop's handle, created while the worker is stuck.
    handle_command("/stop", state=State(path))
    assert work_handle.kill_switch_engaged(), "the halt must be visible to the worker"
    released.set()


def test_main_exposes_the_two_loops():
    from trading_agent import main as m

    assert callable(m.work_loop) and callable(m.command_loop)
    # The command loop must poll far more often than the work loop runs, or
    # /stop inherits the work loop's latency.
    assert m.COMMAND_POLL_SECONDS < m.CYCLE_INTERVAL_SECONDS / 10
