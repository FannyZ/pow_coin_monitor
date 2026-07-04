from __future__ import annotations

import logging
import time
from urllib.parse import quote

from pow_monitor.models import CoinLead, now_iso
from pow_monitor.sources.base import FetchError, http_get_json

logger = logging.getLogger(__name__)


def fetch_coingecko(source_cfg: dict, monitor_cfg: dict) -> list[CoinLead]:
    queries = source_cfg.get("search_queries", ["pow mining"])
    max_per = int(source_cfg.get("max_per_query", 10))
    leads: list[CoinLead] = []
    seen: set[str] = set()

    for q in queries:
        url = f"https://api.coingecko.com/api/v3/search?query={quote(q)}"
        try:
            data = http_get_json(url, monitor_cfg)
        except FetchError as exc:
            logger.warning("CoinGecko search failed (%s): %s", q, exc)
            continue

        time.sleep(float(source_cfg.get("query_delay_sec", 1.2)))

        for item in data.get("coins", [])[:max_per]:
            coin_id = item.get("id", "")
            if not coin_id or coin_id in seen:
                continue
            seen.add(coin_id)
            name = item.get("name", coin_id)
            symbol = (item.get("symbol") or "").upper()
            rank = item.get("market_cap_rank")
            leads.append(
                CoinLead(
                    source="coingecko",
                    title=f"{name} ({symbol}) — CoinGecko search: {q}",
                    url=f"https://www.coingecko.com/en/coins/{coin_id}",
                    summary=f"Search hit for '{q}'" + (f", rank #{rank}" if rank else ""),
                    tags=[symbol.lower(), coin_id],
                    discovered_at=now_iso(),
                    extra={"market_cap_rank": rank},
                )
            )

    logger.info("CoinGecko: %d hits", len(leads))
    return leads
