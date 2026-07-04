from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class CoinStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    fingerprint TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    payload TEXT NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    notified INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    total_leads INTEGER NOT NULL,
                    new_leads INTEGER NOT NULL,
                    meta TEXT NOT NULL
                )
                """
            )

    def upsert_lead(self, lead: dict[str, Any], now: str) -> bool:
        """Returns True if this is a newly seen lead."""
        fp = lead["fingerprint"]
        payload = json.dumps(lead, ensure_ascii=False)
        with self._conn() as conn:
            row = conn.execute("SELECT fingerprint FROM leads WHERE fingerprint = ?", (fp,)).fetchone()
            if row:
                conn.execute(
                    """
                    UPDATE leads SET last_seen = ?, score = ?, payload = ?, title = ?, url = ?
                    WHERE fingerprint = ?
                    """,
                    (now, lead["score"], payload, lead["title"], lead["url"], fp),
                )
                return False
            conn.execute(
                """
                INSERT INTO leads (fingerprint, source, title, url, score, payload, first_seen, last_seen, notified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (fp, lead["source"], lead["title"], lead["url"], lead["score"], payload, now, now),
            )
            return True

    def mark_notified(self, fingerprints: list[str]) -> None:
        if not fingerprints:
            return
        with self._conn() as conn:
            for fp in fingerprints:
                conn.execute("UPDATE leads SET notified = 1 WHERE fingerprint = ?", (fp,))

    def record_scan(self, started_at: str, finished_at: str, total: int, new_count: int, meta: dict) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO scan_runs (started_at, finished_at, total_leads, new_leads, meta)
                VALUES (?, ?, ?, ?, ?)
                """,
                (started_at, finished_at, total, new_count, json.dumps(meta, ensure_ascii=False)),
            )

    def recent_leads(self, limit: int = 50, min_score: int = 0) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT payload FROM leads
                WHERE score >= ?
                ORDER BY last_seen DESC
                LIMIT ?
                """,
                (min_score, limit),
            ).fetchall()
        return [json.loads(r["payload"]) for r in rows]
