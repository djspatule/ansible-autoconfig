"""The model client, and the rule that matters more than its output.

O-02: reasoning runs through opencode on serverannah, so the Pi now depends on
another host. For a process that can hold positions that is a real failure mode,
so losing the backend must mean "open no new positions" — never a retry into a
trade, never a guess.
"""
from __future__ import annotations

import pytest

from trading_agent.reasoning import (
    ReasoningClient,
    ReasoningUnavailable,
    proposals_or_none,
)


def test_unavailable_backend_raises_rather_than_guessing():
    def boom(_payload):
        raise OSError("connection refused")

    with pytest.raises(ReasoningUnavailable):
        ReasoningClient(transport=boom).propose(catalysts=[], positions=[])


def test_unavailable_backend_yields_no_proposals_not_a_default_trade():
    """The safe-wrapper used by the loop: None means do nothing at all."""
    def boom(_payload):
        raise OSError("connection refused")

    assert proposals_or_none(ReasoningClient(transport=boom), catalysts=[], positions=[]) is None


def test_malformed_response_is_rejected_not_coerced():
    """A model that returns nonsense must not be massaged into an order."""
    for junk in ("not json", '{"unexpected": true}', "[]", '{"proposals": "buy"}'):
        client = ReasoningClient(transport=lambda _p, j=junk: j)
        with pytest.raises(ReasoningUnavailable):
            client.propose(catalysts=[], positions=[])


def test_wellformed_response_is_parsed():
    good = '{"proposals": [{"symbol": "MRNA", "side": "buy", "notional_usd": 100, "rationale": "phase 3 readout"}]}'
    client = ReasoningClient(transport=lambda _p: good)
    out = client.propose(catalysts=[], positions=[])
    assert len(out) == 1 and out[0].symbol == "MRNA"


def test_proposal_is_only_a_proposal():
    """It carries no approval token — it must still pass the guardrail."""
    good = '{"proposals": [{"symbol": "MRNA", "side": "buy", "notional_usd": 100, "rationale": "x"}]}'
    out = ReasoningClient(transport=lambda _p: good).propose(catalysts=[], positions=[])
    assert not out[0].to_intent().is_approved
