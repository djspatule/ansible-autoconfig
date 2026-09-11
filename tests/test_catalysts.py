"""Catalyst discovery must degrade, never raise into the loop."""
from __future__ import annotations

from trading_agent.catalysts import CatalystFeed, _parse_study
from trading_agent.universe import Universe


class U:
    def symbols(self):
        return {"MRNA"}


def test_no_transport_configured_yields_nothing():
    feed = CatalystFeed(U())
    assert feed.upcoming_trials() == []
    assert feed.recent_news() == []


def test_a_failing_source_degrades_to_empty(tmp_path):
    def boom(*a, **k):
        raise OSError("ctgov down")

    feed = CatalystFeed(U(), http=boom, news=boom)
    assert feed.upcoming_trials() == []
    assert feed.recent_news() == []


def test_only_late_phase_trials_count():
    early = {"protocolSection": {
        "identificationModule": {"briefTitle": "t", "nctId": "NCT1"},
        "designModule": {"phases": ["PHASE1"]},
        "statusModule": {"primaryCompletionDateStruct": {"date": "2026-10-01"}}}}
    assert _parse_study("MRNA", early) is None

    pivotal = {"protocolSection": {
        "identificationModule": {"briefTitle": "t", "nctId": "NCT2"},
        "designModule": {"phases": ["PHASE3"]},
        "statusModule": {"primaryCompletionDateStruct": {"date": "2026-10-01"}}}}
    c = _parse_study("MRNA", pivotal)
    assert c and c.symbol == "MRNA" and "NCT2" in c.url


def test_a_malformed_study_is_skipped_not_fatal():
    assert _parse_study("MRNA", {"unexpected": True}) is None
