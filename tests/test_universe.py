"""The biotech universe — what the agent is allowed to trade at all."""
from __future__ import annotations

from trading_agent.universe import Universe


def test_seed_universe_is_usable_offline(tmp_path):
    """A cold start with no network must still produce a tradable universe.
    Trading should not stop because a CDN was slow."""
    u = Universe(cache_path=tmp_path / "u.json")
    assert len(u.symbols()) > 10
    assert u.is_biotech("MRNA")


def test_unknown_symbol_is_not_biotech(tmp_path):
    u = Universe(cache_path=tmp_path / "u.json")
    assert not u.is_biotech("AAPL")


def test_symbols_are_normalised(tmp_path):
    u = Universe(cache_path=tmp_path / "u.json")
    assert u.is_biotech("mrna") and u.is_biotech(" MRNA ")


def test_cache_survives_a_restart(tmp_path):
    path = tmp_path / "u.json"
    u = Universe(cache_path=path)
    u._write_cache({"ZZZZ"})
    assert Universe(cache_path=path).is_biotech("ZZZZ")


def test_stale_cache_is_used_rather_than_failing(tmp_path):
    """Explicitly not fatal: a refresh failure must degrade, not halt."""
    path = tmp_path / "u.json"
    u = Universe(cache_path=path)
    u._write_cache({"ZZZZ"})

    def boom(_):
        raise RuntimeError("network down")

    u2 = Universe(cache_path=path, fetcher=boom)
    result = u2.refresh()
    assert result["refreshed"] is False
    assert u2.is_biotech("ZZZZ"), "must fall back to the cached universe"
