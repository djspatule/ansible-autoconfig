"""Materiality and scoreability are separate judgments."""
from __future__ import annotations

from trading_agent.events import Event, EventKind, Materiality, worth_researching


def ev(kind, trial_id=""):
    return Event(symbol="MRNA", kind=kind, title="t", trial_id=trial_id)


def test_earnings_are_not_scored():
    """Quarterly numbers are not the operator's edge; scoring them would
    dilute the one number meant to measure biotech judgment."""
    assert not ev(EventKind.EARNINGS).is_scoreable


def test_trial_events_are_scored():
    for k in (EventKind.TRIAL_READOUT, EventKind.TRIAL_AMENDMENT,
              EventKind.INTERIM_ANALYSIS, EventKind.REGULATORY):
        assert ev(k).is_scoreable


def test_earnings_are_still_surfaced_just_not_researched():
    """Material enough to mention, not worth spending tokens on."""
    e = ev(EventKind.EARNINGS)
    assert e.materiality == Materiality.LOW
    assert not worth_researching(e, has_view=False)


def test_a_held_view_suppresses_further_research():
    """The cheapest token saving there is: a view is the answer research was
    trying to produce."""
    e = ev(EventKind.INTERIM_ANALYSIS)
    assert worth_researching(e, has_view=False)
    assert not worth_researching(e, has_view=True)


def test_a_high_materiality_event_overrides_an_existing_view():
    """An amendment or termination can invalidate an earlier read, so it is
    worth re-examining even when a view exists."""
    assert worth_researching(ev(EventKind.TRIAL_AMENDMENT), has_view=True)
    assert worth_researching(ev(EventKind.TRIAL_READOUT), has_view=True)


def test_views_are_keyed_on_the_trial_not_the_item():
    """One read on a trial should carry across its interim analysis, its
    amendments and its final readout."""
    readout = Event("MRNA", EventKind.TRIAL_READOUT, "t", trial_id="NCT123")
    interim = Event("MRNA", EventKind.INTERIM_ANALYSIS, "t2", trial_id="NCT123")
    assert readout.view_key == interim.view_key == "NCT123"


def test_company_level_events_fall_back_to_the_symbol():
    assert ev(EventKind.EARNINGS).view_key == "MRNA"
