"""Data-source health registry: every provider reports success/failure here.

Used by /status and stamped into every AI prompt so the model knows what is
stale or missing (never fabricates a number that failed to load)."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class SourceHealth:
    name: str
    last_ok: float = 0.0
    last_err: float = 0.0
    error: str = ""
    items: int = 0
    expected_every: int = 600

    @property
    def age(self) -> Optional[float]:
        return time.time() - self.last_ok if self.last_ok else None

    @property
    def state(self) -> str:
        if not self.last_ok:
            return "down" if self.last_err else "pending"
        if self.age > self.expected_every * 3:
            return "stale"
        if self.last_err > self.last_ok:
            return "degraded"
        return "ok"


class Health:
    def __init__(self) -> None:
        self.sources: Dict[str, SourceHealth] = {}

    def _get(self, name: str, every: int) -> SourceHealth:
        if name not in self.sources:
            self.sources[name] = SourceHealth(name, expected_every=every)
        self.sources[name].expected_every = every
        return self.sources[name]

    def ok(self, name: str, items: int = 0, every: int = 600) -> None:
        s = self._get(name, every)
        s.last_ok, s.items = time.time(), items

    def fail(self, name: str, err: Exception | str, every: int = 600) -> None:
        s = self._get(name, every)
        s.last_err, s.error = time.time(), str(err)[:200]

    def summary(self) -> str:
        parts = []
        for s in sorted(self.sources.values(), key=lambda x: x.name):
            age = f"{s.age/60:.0f}m" if s.age is not None else "—"
            parts.append(f"{s.name}:{s.state}({age})")
        return ", ".join(parts)


HEALTH = Health()
