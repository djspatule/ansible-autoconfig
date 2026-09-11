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


# --- the registry is swept on a timer, not every cycle -----------------------

class _Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def _counting_http(counter):
    def http(url, params):
        counter.append(params.get("query.term"))
        return []
    return http


class _Uni:
    def symbols(self):
        return {"MRNA", "BNTX", "VRTX"}


def test_trials_are_not_re_swept_every_cycle():
    calls, clock = [], _Clock()
    feed = CatalystFeed(_Uni(), http=_counting_http(calls), clock=clock)

    feed.upcoming_trials()
    first = len(calls)
    assert first == 3, "one request per symbol on a real sweep"

    for _ in range(10):
        feed.upcoming_trials()
    assert len(calls) == first, "a cached sweep must make no requests"


def test_the_sweep_runs_again_once_the_window_passes():
    calls, clock = [], _Clock()
    feed = CatalystFeed(_Uni(), http=_counting_http(calls),
                        trials_ttl_seconds=3600, clock=clock)
    feed.upcoming_trials()
    clock.t += 3601
    feed.upcoming_trials()
    assert len(calls) == 6
