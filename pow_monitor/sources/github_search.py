from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from pow_monitor.models import CoinLead, now_iso
from pow_monitor.sources.base import FetchError, http_get_json

logger = logging.getLogger(__name__)


def fetch_github(source_cfg: dict, monitor_cfg: dict) -> list[CoinLead]:
    since_days = int(source_cfg.get("since_days", 90))
    since_date = (datetime.now(timezone.utc) - timedelta(days=since_days)).strftime("%Y-%m-%d")
    queries = source_cfg.get("queries", [])
    max_per = int(source_cfg.get("max_per_query", 15))
    leads: list[CoinLead] = []
    seen_urls: set[str] = set()

    for q_template in queries:
        q = q_template.replace("{since}", since_date)
        url = f"https://api.github.com/search/repositories?q={q}&sort=updated&order=desc&per_page={max_per}"
        try:
            data = http_get_json(url, monitor_cfg)
        except FetchError as exc:
            logger.warning("GitHub query failed (%s): %s", q[:40], exc)
            continue

        for item in data.get("items", []):
            html_url = item.get("html_url", "")
            if not html_url or html_url in seen_urls:
                continue
            seen_urls.add(html_url)
            name = item.get("full_name") or item.get("name") or "unknown"
            desc = item.get("description") or ""
            topics = item.get("topics") or []
            leads.append(
                CoinLead(
                    source="github",
                    title=f"{name} — {desc[:80]}".strip(" —"),
                    url=html_url,
                    summary=desc,
                    tags=topics,
                    discovered_at=now_iso(),
                    extra={
                        "github": html_url,
                        "homepage": item.get("homepage") or "",
                        "stars": item.get("stargazers_count", 0),
                        "updated_at": item.get("updated_at", ""),
                        "language": item.get("language", ""),
                    },
                )
            )

    logger.info("GitHub: %d repos", len(leads))
    return leads
