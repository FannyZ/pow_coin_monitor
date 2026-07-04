from __future__ import annotations

import logging

from pow_monitor.baseline import SourceBaseline
from pow_monitor.config import ROOT
from pow_monitor.models import CoinLead, now_iso
from pow_monitor.sources.base import FetchError, http_get_json

logger = logging.getLogger(__name__)


def fetch_rainbowminer(source_cfg: dict, monitor_cfg: dict) -> list[CoinLead]:
    url = source_cfg.get(
        "url",
        "https://raw.githubusercontent.com/RainbowMiner/RainbowMiner/master/Data/coinsdb.json",
    )
    max_coins = int(source_cfg.get("max_coins", 30))
    baseline = SourceBaseline(ROOT / source_cfg.get("baseline_path", "data/rainbowminer_baseline.json"))
    leads: list[CoinLead] = []

    try:
        data = http_get_json(url, monitor_cfg, referer="https://github.com/")
    except FetchError as exc:
        logger.warning("RainbowMiner coinsdb fetch failed: %s", exc)
        return leads

    if not isinstance(data, dict):
        return leads

    new_keys = baseline.filter_new("rainbowminer", data.keys())
    for key in sorted(new_keys)[:max_coins]:
        info = data.get(key) or {}
        if not isinstance(info, dict):
            info = {}
        name = str(info.get("Name") or info.get("name") or key)
        algo = str(info.get("Algorithm") or info.get("algorithm") or "")
        symbol = str(info.get("Symbol") or info.get("symbol") or key)
        leads.append(
            CoinLead(
                source="rainbowminer",
                title=f"{name} ({symbol}) — new in RainbowMiner DB",
                url="https://github.com/RainbowMiner/RainbowMiner",
                summary=f"New coin entry in RainbowMiner coinsdb.json — algo: {algo or 'unknown'}",
                tags=[symbol.lower(), algo.lower(), "rainbowminer", "pool-tracker"],
                discovered_at=now_iso(),
                extra={"key": key, "algorithm": algo},
            )
        )

    logger.info("RainbowMiner: %d coins tracked, %d new", len(data), len(leads))
    return leads
