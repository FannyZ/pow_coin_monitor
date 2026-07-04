from __future__ import annotations

import logging
import re

from bs4 import BeautifulSoup

from pow_monitor.models import CoinLead, now_iso
from pow_monitor.sources.base import FetchError, http_get

logger = logging.getLogger(__name__)


def fetch_safetrade(source_cfg: dict, monitor_cfg: dict) -> list[CoinLead]:
    url = source_cfg.get("url", "https://safetrade.com/")
    max_ann = int(source_cfg.get("max_announcements", 20))
    leads: list[CoinLead] = []

    try:
        html = http_get(url, monitor_cfg)
    except FetchError as exc:
        logger.warning("SafeTrade fetch failed: %s", exc)
        return leads

    soup = BeautifulSoup(html, "lxml")
    seen: set[str] = set()

    # Announcement lines like "Pearl ($PRL) has been listed on SafeTrade!2026-05-20"
    text_blocks = soup.get_text("\n", strip=True)
    for line in text_blocks.split("\n"):
        if "listed on SafeTrade" not in line and "has been listed" not in line:
            continue
        m = re.match(r"(.+?)\s+has been listed on SafeTrade!?\s*(\d{4}-\d{2}-\d{2})?", line, re.I)
        if not m:
            continue
        title = m.group(1).strip()
        date = m.group(2) or ""
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        leads.append(
            CoinLead(
                source="safetrade",
                title=f"{title} listed on SafeTrade {date}".strip(),
                url=url,
                summary=line[:200],
                discovered_at=now_iso(),
                extra={"listing_date": date},
            )
        )
        if len(leads) >= max_ann:
            break

    logger.info("SafeTrade: %d announcements", len(leads))
    return leads
