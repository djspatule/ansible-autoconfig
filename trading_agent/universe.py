"""What the agent may trade.

Derived from biotech ETF holdings (XBI, IBB) rather than a hand-kept list: the
operator was clear that a manual list is too large and too time-dependent to
maintain, and an ETF's published holdings are already curated, auditable and
self-updating.

A seed list ships in-tree so a cold start works with no network. Refreshing is
explicit and never fatal — a slow CDN must not stop trading.
"""
from __future__ import annotations

import json
from pathlib import Path

# Seed only. Large, liquid biotech names so a cold start is tradable before the
# first successful refresh; the real universe comes from the ETF holdings.
_SEED = {
    "MRNA", "BNTX", "REGN", "VRTX", "GILD", "AMGN", "BIIB", "ILMN", "INCY",
    "ALNY", "BMRN", "NBIX", "SRPT", "IONS", "EXAS", "TECH", "RARE", "FOLD",
    "ARWR", "BEAM", "NTLA", "CRSP", "EDIT", "VCYT", "HALO", "UTHR", "JAZZ",
    "XBI", "IBB",
}


class Universe:
    def __init__(self, cache_path: Path | str, fetcher=None) -> None:
        self.cache_path = Path(cache_path)
        self._fetcher = fetcher
        self._symbols = self._read_cache() or set(_SEED)

    def symbols(self) -> set[str]:
        return set(self._symbols)

    def is_biotech(self, symbol: str) -> bool:
        return (symbol or "").strip().upper() in self._symbols

    def refresh(self) -> dict:
        """Pull fresh holdings. Failure degrades to the cache, never raises."""
        if self._fetcher is None:
            return {"refreshed": False, "reason": "no fetcher configured",
                    "count": len(self._symbols)}
        try:
            fetched = {s.strip().upper() for s in self._fetcher(None) if s.strip()}
        except Exception as exc:  # noqa: BLE001 — degrade, do not halt
            return {"refreshed": False, "reason": str(exc),
                    "count": len(self._symbols)}
        if not fetched:
            # An empty result is far more likely to be a broken parse than a
            # genuinely empty ETF, and adopting it would silently forbid
            # everything.
            return {"refreshed": False, "reason": "empty result ignored",
                    "count": len(self._symbols)}
        self._write_cache(fetched)
        return {"refreshed": True, "count": len(fetched)}

    def _read_cache(self) -> set[str] | None:
        try:
            data = json.loads(self.cache_path.read_text())
            return {s.upper() for s in data["symbols"]} or None
        except Exception:  # noqa: BLE001 — a missing or corrupt cache is normal
            return None

    def _write_cache(self, symbols: set[str]) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps({"symbols": sorted(symbols)}))
        self._symbols = set(symbols)
