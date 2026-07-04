from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


class SourceBaseline:
    """Track known IDs per aggregate source so first run does not flood alerts."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            self.data: dict[str, list[str]] = json.loads(path.read_text(encoding="utf-8"))
        else:
            self.data = {}

    def _save(self) -> None:
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def filter_new(self, source: str, ids: Iterable[str]) -> set[str]:
        current = {str(i) for i in ids if i}
        known = set(self.data.get(source, []))
        if not known:
            self.data[source] = sorted(current)
            self._save()
            return set()
        new_ids = current - known
        if new_ids:
            known.update(new_ids)
            self.data[source] = sorted(known)
            self._save()
        return new_ids
