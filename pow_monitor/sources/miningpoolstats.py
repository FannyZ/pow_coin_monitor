from __future__ import annotations

import logging
import re
from urllib.parse import urljoin

from pow_monitor.baseline import SourceBaseline
from pow_monitor.config import ROOT
from pow_monitor.models import CoinLead, now_iso
from pow_monitor.sources.base import FetchError, http_get

logger = logging.getLogger(__name__)

SKIP_SLUGS = {
    "",
    "about",
    "contact",
    "login",
    "register",
    "privacy",
    "terms",
    "cache",
}


def _parse_sitemap_slugs(xml: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for match in re.finditer(r"<loc>https://miningpoolstats\.stream/([^<]+)</loc>", xml, re.I):
        slug = match.group(1).strip().strip("/")
        if not slug or "/" in slug or slug in SKIP_SLUGS:
            continue
        url = f"https://miningpoolstats.stream/{slug}"
        entries.append((slug, url))
    return entries


def fetch_miningpoolstats(source_cfg: dict, monitor_cfg: dict) -> list[CoinLead]:
    base = source_cfg.get("url", "https://miningpoolstats.stream/")
    sitemap_url = source_cfg.get("sitemap_url", "https://miningpoolstats.stream/sitemap.xml")
    max_coins = int(source_cfg.get("max_coins", 50))
    baseline = SourceBaseline(ROOT / source_cfg.get("baseline_path", "data/mps_baseline.json"))
    leads: list[CoinLead] = []

    try:
        xml = http_get(sitemap_url, monitor_cfg, referer=base)
    except FetchError as exc:
        logger.warning("MiningPoolStats sitemap fetch failed: %s", exc)
        return leads

    entries = _parse_sitemap_slugs(xml)
    if not entries:
        logger.warning("MiningPoolStats: sitemap parsed 0 coin slugs")
        return leads

    new_slugs = baseline.filter_new("miningpoolstats", [slug for slug, _ in entries])
    slug_to_url = dict(entries)

    for slug in sorted(new_slugs)[:max_coins]:
        full = slug_to_url[slug]
        title = slug.replace("-", " ").title()
        leads.append(
            CoinLead(
                source="miningpoolstats",
                title=f"{title} ({slug}) — new on MiningPoolStats",
                url=full,
                summary=f"New coin page detected on MiningPoolStats: {slug}",
                tags=[slug, "miningpoolstats"],
                discovered_at=now_iso(),
            )
        )

    logger.info(
        "MiningPoolStats: %d total slugs, %d new leads (capped %d)",
        len(entries),
        len(leads),
        max_coins,
    )
    return leads
