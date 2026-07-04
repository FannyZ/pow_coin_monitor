from __future__ import annotations

import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from pow_monitor.models import CoinLead, now_iso
from pow_monitor.sources.base import FetchError, http_get

logger = logging.getLogger(__name__)


def fetch_bitcointalk(source_cfg: dict, monitor_cfg: dict) -> list[CoinLead]:
    url = source_cfg.get("url", "https://bitcointalk.org/index.php?board=159.0")
    max_topics = int(source_cfg.get("max_topics", 40))
    leads: list[CoinLead] = []

    try:
        html = http_get(url, monitor_cfg)
    except FetchError as exc:
        logger.warning("BitcoinTalk fetch failed: %s", exc)
        return leads

    soup = BeautifulSoup(html, "lxml")
    rows = soup.select("tr")
    seen = set()

    for row in rows:
        link = row.select_one("span.subject a")
        if not link or not link.get("href"):
            continue
        title = link.get_text(strip=True)
        if not title or len(title) < 8:
            continue
        href = link["href"]
        if not href.startswith("http"):
            href = urljoin("https://bitcointalk.org/", href)
        if href in seen:
            continue
        seen.add(href)

        # Skip sticky/meta threads
        if title.lower().startswith("rules") or "report malware" in title.lower():
            continue

        leads.append(
            CoinLead(
                source="bitcointalk",
                title=title,
                url=href,
                summary=title,
                discovered_at=now_iso(),
            )
        )
        if len(leads) >= max_topics:
            break

    logger.info("BitcoinTalk: %d topics", len(leads))
    return leads
