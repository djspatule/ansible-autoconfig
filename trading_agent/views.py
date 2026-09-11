"""Operator views: predictions recorded before outcomes are known.

This is the alpha source. The agent does not guess at clinical trial outcomes —
the operator judges, and the agent executes with discipline. A catalyst with no
stored view is simply not traded.

The ordering is what makes it valuable twice over: recorded before the event it
is a trading signal, and after the event it is a measurable prediction. Scoring
those is the point — the operator's stated objective is learning the field, and
"9 of 12 phase-3 oncology readouts" is worth more than any model output.
"""
from __future__ import annotations

import datetime as dt
import sqlite3
from dataclasses import dataclass
from pathlib import Path

# A stance the operator can actually hold. "no_opinion" is deliberately one of
# them: not knowing is information, and it must be distinguishable from never
# having been asked.
STANCES = ("positive", "negative", "no_opinion")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS views (
    symbol TEXT NOT NULL,
    event_id TEXT NOT NULL,
    stance TEXT NOT NULL,
    confidence INTEGER NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    recorded_at TEXT NOT NULL,
    expires_at TEXT,
    PRIMARY KEY (symbol, event_id, recorded_at)
);
CREATE TABLE IF NOT EXISTS outcomes (
    symbol TEXT NOT NULL,
    event_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    PRIMARY KEY (symbol, event_id)
);
"""


@dataclass(frozen=True)
class View:
    symbol: str
    event_id: str
    stance: str
    confidence: int          # 0-5; 0 goes with no_opinion
    note: str
    recorded_at: dt.datetime
    expires_at: dt.datetime | None = None

    @property
    def is_actionable(self) -> bool:
        """Only a held opinion licenses a trade. 'no_opinion' does not."""
        return self.stance in ("positive", "negative")

    @property
    def side(self) -> str | None:
        """v1 is long-only, so a negative view means 'do not buy' rather than
        'short'. Shorting arrives with puts in v2."""
        return "buy" if self.stance == "positive" else None


class ViewStore:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(self.path, isolation_level=None)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.executescript(_SCHEMA)

    def record(self, view: View) -> None:
        self._db.execute(
            "INSERT OR REPLACE INTO views"
            "(symbol,event_id,stance,confidence,note,recorded_at,expires_at)"
            " VALUES(?,?,?,?,?,?,?)",
            (view.symbol.upper(), view.event_id, view.stance, view.confidence,
             view.note, view.recorded_at.isoformat(),
             view.expires_at.isoformat() if view.expires_at else None),
        )

    def for_event(self, symbol: str, event_id: str, *,
                  now: dt.datetime) -> View | None:
        """The most recent unexpired view, or None.

        None means *no view*, never a neutral default — the caller must not be
        able to mistake silence for permission.
        """
        row = self._db.execute(
            "SELECT symbol,event_id,stance,confidence,note,recorded_at,expires_at"
            " FROM views WHERE symbol=? AND event_id=?"
            " ORDER BY recorded_at DESC LIMIT 1",
            (symbol.upper(), event_id),
        ).fetchone()
        if not row:
            return None
        expires = dt.datetime.fromisoformat(row[6]) if row[6] else None
        # A read on a readout is about that readout. Letting it age into a
        # standing licence is how a stale opinion funds a trade months later.
        if expires and now >= expires:
            return None
        return View(row[0], row[1], row[2], int(row[3]), row[4],
                    dt.datetime.fromisoformat(row[5]), expires)

    def record_outcome(self, symbol: str, event_id: str, outcome: str,
                       observed_at: dt.datetime) -> None:
        self._db.execute(
            "INSERT OR REPLACE INTO outcomes(symbol,event_id,outcome,observed_at)"
            " VALUES(?,?,?,?)",
            (symbol.upper(), event_id, outcome, observed_at.isoformat()),
        )

    def scored(self) -> list[dict]:
        """Views that now have an outcome. 'no_opinion' is excluded — scoring
        honesty as a miss would make the scoreboard useless."""
        rows = self._db.execute(
            "SELECT v.symbol, v.event_id, v.stance, v.confidence, o.outcome"
            " FROM views v JOIN outcomes o"
            "   ON v.symbol=o.symbol AND v.event_id=o.event_id"
            " WHERE v.stance != 'no_opinion'"
            " GROUP BY v.symbol, v.event_id"
            " HAVING v.recorded_at = MAX(v.recorded_at)"
        ).fetchall()
        return [
            {"symbol": r[0], "event_id": r[1], "stance": r[2],
             "confidence": int(r[3]), "outcome": r[4], "correct": r[2] == r[4]}
            for r in rows
        ]

    # Published base rates for trial success by phase. Being right 55% of the
    # time is only an edge if chance would have been 50% — an accuracy number
    # with nothing to compare it against says nothing at all, which is the
    # whole point of measuring.
    #
    # Approximate and worth revisiting against a real source; they exist to
    # give the scoreboard a denominator, not to be precise.
    BASE_RATES = {"PHASE1": 0.52, "PHASE2": 0.29, "PHASE3": 0.58, "": 0.50}

    def scoreboard(self, *, base_rate: float | None = None) -> dict:
        s = self.scored()
        correct = sum(1 for r in s if r["correct"])
        by_conf: dict[int, dict] = {}
        for r in s:
            b = by_conf.setdefault(r["confidence"], {"n": 0, "correct": 0})
            b["n"] += 1
            b["correct"] += 1 if r["correct"] else 0
        accuracy = (correct / len(s)) if s else None
        base = self.BASE_RATES[""] if base_rate is None else base_rate
        return {
            "scored": len(s),
            "correct": correct,
            "accuracy": accuracy,
            "base_rate": base,
            # The number that actually matters. Positive means judgment is
            # adding something over chance; zero or negative means the effort
            # is not yet paying, however pleasant the raw accuracy looks.
            "edge_over_base": (accuracy - base) if accuracy is not None else None,
            # A caveat rather than a statistic. Under roughly thirty scored
            # calls, an "edge" is mostly noise, and reporting it without saying
            # so would be the most misleading thing this file could do.
            "significant": len(s) >= 30,
            # Whether confidence tracks accuracy is the most useful breakdown:
            # being right often matters less than knowing when you are right.
            "by_confidence": by_conf,
        }
