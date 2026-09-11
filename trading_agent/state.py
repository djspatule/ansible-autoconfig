"""Durable safety state.

Everything here must survive a restart, because the things it holds are exactly
the things you cannot afford to forget: whether trading is halted, how much has
already been risked today, and which decisions are still in flight.

SQLite rather than JSON: the Telegram handler and the reasoning loop touch this
concurrently, and an interrupted write to a JSON file is a corrupted file
whereas an interrupted SQLite transaction is a rolled-back one.
"""
from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS flags (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY, day TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS daily (
    day TEXT PRIMARY KEY,
    pnl_usd REAL NOT NULL DEFAULT 0.0,
    -- Latched separately from pnl: once the breaker trips the day is over,
    -- even if the position recovers. A breaker that un-trips is not a breaker.
    loss_breaker_tripped INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS approvals (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
"""


def _day(now: dt.datetime) -> str:
    return now.date().isoformat()


class State:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(self.path, isolation_level=None)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.executescript(_SCHEMA)

    # --- kill switch --------------------------------------------------------

    def set_kill_switch(self, engaged: bool) -> None:
        self._db.execute(
            "INSERT INTO flags(key,value) VALUES('kill_switch',?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            ("1" if engaged else "0",),
        )

    def kill_switch_engaged(self) -> bool:
        row = self._db.execute(
            "SELECT value FROM flags WHERE key='kill_switch'"
        ).fetchone()
        return bool(row and row[0] == "1")

    # --- trade rate ---------------------------------------------------------

    def record_trade(self, now: dt.datetime) -> None:
        self._db.execute("INSERT INTO trades(day) VALUES(?)", (_day(now),))

    def trades_today(self, now: dt.datetime) -> int:
        row = self._db.execute(
            "SELECT COUNT(*) FROM trades WHERE day=?", (_day(now),)
        ).fetchone()
        return int(row[0]) if row else 0

    # --- capital and P&L ----------------------------------------------------

    def set_deployed_usd(self, amount: float) -> None:
        self._db.execute(
            "INSERT INTO flags(key,value) VALUES('deployed',?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (str(amount),),
        )

    def deployed_usd(self) -> float:
        row = self._db.execute(
            "SELECT value FROM flags WHERE key='deployed'"
        ).fetchone()
        return float(row[0]) if row else 0.0

    def set_daily_pnl_usd(self, pnl: float, now: dt.datetime) -> None:
        self._db.execute(
            "INSERT INTO daily(day,pnl_usd) VALUES(?,?) "
            "ON CONFLICT(day) DO UPDATE SET pnl_usd=excluded.pnl_usd",
            (_day(now), pnl),
        )

    def daily_pnl_usd(self, now: dt.datetime) -> float:
        row = self._db.execute(
            "SELECT pnl_usd FROM daily WHERE day=?", (_day(now),)
        ).fetchone()
        return float(row[0]) if row else 0.0

    def trip_loss_breaker(self, now: dt.datetime) -> None:
        self._db.execute(
            "INSERT INTO daily(day,pnl_usd,loss_breaker_tripped) VALUES(?,0.0,1) "
            "ON CONFLICT(day) DO UPDATE SET loss_breaker_tripped=1",
            (_day(now),),
        )

    def loss_breaker_tripped(self, now: dt.datetime) -> bool:
        row = self._db.execute(
            "SELECT loss_breaker_tripped FROM daily WHERE day=?", (_day(now),)
        ).fetchone()
        return bool(row and row[0])

    # --- pending approvals --------------------------------------------------

    def add_pending_approval(self, request_id: str, payload: dict) -> None:
        self._db.execute(
            "INSERT INTO approvals(id,payload) VALUES(?,?) "
            "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
            (request_id, json.dumps(payload)),
        )

    def pending_approvals(self) -> dict[str, dict]:
        return {
            r[0]: json.loads(r[1])
            for r in self._db.execute("SELECT id,payload FROM approvals")
        }

    def resolve_approval(self, request_id: str) -> None:
        self._db.execute("DELETE FROM approvals WHERE id=?", (request_id,))
