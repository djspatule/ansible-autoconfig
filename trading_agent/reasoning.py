"""The model client.

Thin on purpose. The backend is opencode on serverannah so the provider can be
swapped without touching this code, and nothing provider-specific is allowed to
leak past this module.

The important behaviour is not what it returns but what it does when it cannot
return anything: it raises, and the loop opens no positions. A trading process
that guesses when its reasoning is unavailable is worse than one that stops.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from trading_agent.guardrails import OrderIntent


class ReasoningUnavailable(RuntimeError):
    """Backend unreachable, or its answer unusable. Callers must not trade."""


@dataclass(frozen=True)
class Proposal:
    symbol: str
    side: str
    notional_usd: float
    rationale: str
    correlation_id: str = ""

    def to_intent(self) -> OrderIntent:
        # Deliberately unapproved. A proposal is an opinion; only the guardrail
        # can turn one into something the broker will accept.
        return OrderIntent(
            symbol=self.symbol,
            side=self.side,
            notional_usd=self.notional_usd,
            correlation_id=self.correlation_id,
        )


class ReasoningClient:
    def __init__(self, transport, *, url: str = "") -> None:
        self._transport = transport
        self.url = url

    @classmethod
    def from_config(cls, config) -> "ReasoningClient":
        import httpx

        def transport(payload: dict) -> str:
            r = httpx.post(config.opencode_url, json=payload, timeout=60.0)
            r.raise_for_status()
            return r.text

        return cls(transport, url=config.opencode_url)

    def propose(self, *, catalysts, positions) -> list[Proposal]:
        payload = {"catalysts": catalysts, "positions": positions}
        try:
            raw = self._transport(payload)
        except Exception as exc:  # noqa: BLE001 — every failure is fail-closed
            raise ReasoningUnavailable(f"backend unreachable: {exc}") from exc

        try:
            data = json.loads(raw)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ReasoningUnavailable(f"unparseable response: {exc}") from exc

        if not isinstance(data, dict) or "proposals" not in data:
            raise ReasoningUnavailable("response missing 'proposals'")
        items = data["proposals"]
        if not isinstance(items, list):
            raise ReasoningUnavailable("'proposals' is not a list")

        out: list[Proposal] = []
        for item in items:
            try:
                out.append(Proposal(
                    symbol=str(item["symbol"]).strip().upper(),
                    side=str(item["side"]).strip().lower(),
                    notional_usd=float(item["notional_usd"]),
                    rationale=str(item.get("rationale", "")),
                    correlation_id=str(item.get("correlation_id", "")),
                ))
            except (KeyError, TypeError, ValueError) as exc:
                # Reject the batch rather than the item: a malformed response
                # suggests a confused model, and cherry-picking the parseable
                # half of a confused answer is how you trade on nonsense.
                raise ReasoningUnavailable(f"malformed proposal {item!r}: {exc}") from exc
        return out


def proposals_or_none(client: ReasoningClient, **kwargs):
    """Loop-facing wrapper. None means do nothing — never a default trade."""
    try:
        return client.propose(**kwargs)
    except ReasoningUnavailable:
        return None
