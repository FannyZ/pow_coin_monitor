from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class CoinLead:
    """A candidate new mineable coin from any source."""

    source: str
    title: str
    url: str
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    score: int = 0
    score_reasons: list[str] = field(default_factory=list)
    discovered_at: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def fingerprint(self) -> str:
        """Stable id for dedup across runs."""
        key = f"{self.source}|{self.url.strip().lower()}|{self.title.strip().lower()[:120]}"
        return key

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "title": self.title,
            "url": self.url,
            "summary": self.summary,
            "tags": self.tags,
            "score": self.score,
            "score_reasons": self.score_reasons,
            "discovered_at": self.discovered_at,
            "fingerprint": self.fingerprint,
            "extra": self.extra,
        }


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
