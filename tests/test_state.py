"""ACCEPTANCE B1, C2 — safety state must survive a restart."""
from __future__ import annotations

import datetime as dt

from trading_agent.state import State

NOW = dt.datetime(2026, 9, 11, 15, 0, tzinfo=dt.timezone.utc)


def test_b1_kill_switch_survives_restart(tmp_path):
    path = tmp_path / "s.db"
    State(path).set_kill_switch(True)
    assert State(path).kill_switch_engaged() is True, "must be on disk, not in memory"


def test_b3_only_explicit_resume_clears_it(tmp_path):
    path = tmp_path / "s.db"
    s = State(path)
    s.set_kill_switch(True)
    assert s.kill_switch_engaged()
    s.set_kill_switch(False)
    assert not s.kill_switch_engaged()


def test_c2_pending_approval_survives_restart(tmp_path):
    path = tmp_path / "s.db"
    State(path).add_pending_approval("req1", {"symbol": "XBI"})
    assert "req1" in State(path).pending_approvals()


def test_trade_counter_is_per_day(tmp_path):
    s = State(tmp_path / "s.db")
    s.record_trade(NOW)
    s.record_trade(NOW)
    assert s.trades_today(NOW) == 2
    assert s.trades_today(NOW + dt.timedelta(days=1)) == 0
