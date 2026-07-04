from __future__ import annotations

import logging

from pow_monitor.baseline import SourceBaseline
from pow_monitor.config import ROOT
from pow_monitor.models import CoinLead, now_iso
from pow_monitor.sources.base import FetchError, http_get_json

logger = logging.getLogger(__name__)


def fetch_nicehash(source_cfg: dict, monitor_cfg: dict) -> list[CoinLead]:
    url = source_cfg.get("url", "https://api2.nicehash.com/main/api/v2/mining/algorithms")
    max_items = int(source_cfg.get("max_items", 20))
    baseline = SourceBaseline(ROOT / source_cfg.get("baseline_path", "data/nicehash_baseline.json"))
    leads: list[CoinLead] = []

    try:
        data = http_get_json(url, monitor_cfg, referer="https://www.nicehash.com/")
    except FetchError as exc:
        logger.warning("NiceHash algorithms fetch failed: %s", exc)
        return leads

    items = data if isinstance(data, list) else data.get("miningAlgorithms") or data.get("algorithms") or []
    if not isinstance(items, list):
        return leads

    ids = []
    by_id: dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        algo_id = str(item.get("algorithm") or item.get("name") or item.get("title") or "")
        if algo_id:
            ids.append(algo_id)
            by_id[algo_id] = item

    new_ids = baseline.filter_new("nicehash", ids)
    for algo_id in sorted(new_ids)[:max_items]:
        item = by_id[algo_id]
        title = str(item.get("title") or item.get("name") or algo_id)
        leads.append(
            CoinLead(
                source="nicehash",
                title=f"NiceHash new algorithm: {title}",
                url="https://www.nicehash.com/algorithm",
                summary=f"New mining algorithm on NiceHash: {title}",
                tags=[title.lower(), "nicehash", "algorithm"],
                discovered_at=now_iso(),
                extra={"algorithm": algo_id},
            )
        )

    logger.info("NiceHash: %d algorithms tracked, %d new", len(ids), len(leads))
    return leads
