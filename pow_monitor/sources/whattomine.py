from __future__ import annotations

import logging

from pow_monitor.baseline import SourceBaseline
from pow_monitor.config import ROOT
from pow_monitor.models import CoinLead, now_iso
from pow_monitor.sources.base import FetchError, http_get_json

logger = logging.getLogger(__name__)

GPU_ALGORITHMS = {
    "kawpow",
    "progpow",
    "progpowz",
    "ethash",
    "etchash",
    "autolykos",
    "autolykos2",
    "blake3",
    "octopus",
    "firopow",
    "beamhash",
    "zelhash",
    "kheavyhash",
    "nexapow",
    "dynexsolve",
    "x16r",
    "x16rv2",
    "x16s",
    "x16rt",
    "equihash",
    "equihash125",
    "equihash144",
    "equihash192",
    "equihash210",
    "cuckatoo32",
    "cuckoo",
    "verthash",
    "randomx",
    "matmul",
}


def fetch_whattomine(source_cfg: dict, monitor_cfg: dict) -> list[CoinLead]:
    url = source_cfg.get("url", "https://whattomine.com/coins.json")
    max_coins = int(source_cfg.get("max_coins", 30))
    baseline = SourceBaseline(ROOT / source_cfg.get("baseline_path", "data/wtm_baseline.json"))
    leads: list[CoinLead] = []

    try:
        data = http_get_json(url, monitor_cfg, referer="https://whattomine.com/")
    except FetchError as exc:
        logger.warning("WhatToMine fetch failed: %s", exc)
        return leads

    coins = data.get("coins") or {}
    gpu_entries: list[tuple[str, dict]] = []
    for name, info in coins.items():
        algo = str(info.get("algorithm", "")).lower()
        if any(g in algo for g in GPU_ALGORITHMS):
            tag = str(info.get("tag") or name)
            gpu_entries.append((tag, info))

    new_tags = baseline.filter_new("whattomine", [tag for tag, _ in gpu_entries])
    info_by_tag = {tag: info for tag, info in gpu_entries}

    for tag in sorted(new_tags)[:max_coins]:
        info = info_by_tag[tag]
        algo = info.get("algorithm", "")
        coin_id = info.get("id", "")
        url = f"https://whattomine.com/coins/{coin_id}.json"
        leads.append(
            CoinLead(
                source="whattomine",
                title=f"{info.get('name', tag)} ({tag}) — GPU {algo}",
                url=url,
                summary=f"New GPU-mineable coin on WhatToMine: {tag}, algorithm {algo}",
                tags=[tag.lower(), algo.lower(), "gpu", "whattomine"],
                discovered_at=now_iso(),
                extra={"coin_id": coin_id, "algorithm": algo},
            )
        )

    logger.info(
        "WhatToMine: %d GPU coins tracked, %d new leads",
        len(gpu_entries),
        len(leads),
    )
    return leads
