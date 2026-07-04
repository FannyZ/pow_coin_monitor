from __future__ import annotations

import logging

from pow_monitor.baseline import SourceBaseline
from pow_monitor.config import ROOT
from pow_monitor.models import CoinLead, now_iso
from pow_monitor.sources.base import FetchError, http_get_json

logger = logging.getLogger(__name__)


def _lead_from_yiimp(source: str, ticker: str, info: dict, pool_url: str) -> CoinLead:
    algo = str(info.get("algo") or info.get("algorithm") or "")
    name = str(info.get("name") or ticker)
    port = info.get("port") or info.get("stratum_port")
    site = str(info.get("site") or "")
    explorer = str(info.get("explorer") or "")
    summary_parts = [f"Algorithm: {algo}" if algo else "", f"Port: {port}" if port else ""]
    summary = ", ".join(p for p in summary_parts if p)
    url = site or explorer or pool_url
    tags = [ticker.lower(), algo.lower(), "yiimp", "pool"]
    return CoinLead(
        source=source,
        title=f"{name} ({ticker}) — new on {source}",
        url=url,
        summary=summary or f"New coin on pool API: {ticker}",
        tags=tags,
        discovered_at=now_iso(),
        extra={"ticker": ticker, "algo": algo, "port": port, "pool": source},
    )


def fetch_yiimp_pools(source_cfg: dict, monitor_cfg: dict) -> list[CoinLead]:
    pools = source_cfg.get("pools", [])
    max_coins = int(source_cfg.get("max_coins", 30))
    baseline = SourceBaseline(ROOT / source_cfg.get("baseline_path", "data/yiimp_baseline.json"))
    leads: list[CoinLead] = []

    for pool in pools:
        if not pool.get("enabled", True):
            continue
        name = pool.get("name", "yiimp")
        url = pool["url"]
        try:
            data = http_get_json(url, monitor_cfg, referer=pool.get("referer"))
        except FetchError as exc:
            logger.warning("YiiMP pool %s fetch failed: %s", name, exc)
            continue

        if not isinstance(data, dict):
            logger.warning("YiiMP pool %s returned non-dict payload", name)
            continue

        new_tickers = baseline.filter_new(name, data.keys())
        for ticker in sorted(new_tickers)[:max_coins]:
            info = data.get(ticker) or {}
            if not isinstance(info, dict):
                info = {}
            leads.append(_lead_from_yiimp(name, ticker, info, url))

        logger.info("YiiMP %s: %d coins tracked, %d new", name, len(data), len(new_tickers))

    return leads[:max_coins]
