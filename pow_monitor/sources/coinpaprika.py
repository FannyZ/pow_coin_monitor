from __future__ import annotations

import logging

from pow_monitor.baseline import SourceBaseline
from pow_monitor.config import ROOT
from pow_monitor.models import CoinLead, now_iso
from pow_monitor.sources.base import FetchError, http_get_json

logger = logging.getLogger(__name__)


def fetch_coinpaprika(source_cfg: dict, monitor_cfg: dict) -> list[CoinLead]:
    url = source_cfg.get("url", "https://api.coinpaprika.com/v1/coins")
    max_coins = int(source_cfg.get("max_coins", 30))
    only_new = bool(source_cfg.get("only_new", True))
    baseline = SourceBaseline(ROOT / source_cfg.get("baseline_path", "data/coinpaprika_baseline.json"))
    leads: list[CoinLead] = []

    try:
        data = http_get_json(url, monitor_cfg)
    except FetchError as exc:
        logger.warning("CoinPaprika fetch failed: %s", exc)
        return leads

    if not isinstance(data, list):
        return leads

    candidates = []
    for coin in data:
        if coin.get("type") != "coin":
            continue
        if only_new and not coin.get("is_new"):
            continue
        coin_id = coin.get("id", "")
        if coin_id:
            candidates.append(coin)

    new_ids = baseline.filter_new("coinpaprika", [c["id"] for c in candidates])
    for coin in candidates:
        if coin["id"] not in new_ids:
            continue
        symbol = (coin.get("symbol") or "").upper()
        name = coin.get("name") or symbol
        coin_id = coin["id"]
        leads.append(
            CoinLead(
                source="coinpaprika",
                title=f"{name} ({symbol}) — new on CoinPaprika",
                url=f"https://coinpaprika.com/coin/{coin_id}/",
                summary="Recently added coin on CoinPaprika (is_new within ~5 days)",
                tags=[symbol.lower(), "coinpaprika", "aggregator"],
                discovered_at=now_iso(),
                extra={"coin_id": coin_id, "is_new": coin.get("is_new")},
            )
        )
        if len(leads) >= max_coins:
            break

    logger.info("CoinPaprika: %d candidates, %d new leads", len(candidates), len(leads))
    return leads
