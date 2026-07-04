from __future__ import annotations

from pow_monitor.models import CoinLead


def score_lead(lead: CoinLead, keywords: dict) -> CoinLead:
    text = f"{lead.title} {lead.summary} {' '.join(lead.tags)}".lower()
    reasons: list[str] = []
    score = 0

    for kw in keywords.get("negative", []):
        if kw.lower() in text:
            score -= 15
            reasons.append(f"-{kw}")

    for kw in keywords.get("high", []):
        if kw.lower() in text:
            score += 12
            reasons.append(kw)

    for kw in keywords.get("medium", []):
        if kw.lower() in text:
            score += 5
            reasons.append(kw)

    # Source bonuses
    if lead.source == "bitcointalk":
        if "[pre-ann]" in text or "pre-ann" in text:
            score += 15
            reasons.append("PRE-ANN")
        if "mainnet" in text:
            score += 10
            reasons.append("mainnet")
    if lead.source == "github":
        score += 8
        reasons.append("github_repo")
    if lead.source == "miningpoolstats":
        score += 10
        reasons.append("has_pool")
    if lead.source == "safetrade":
        score += 12
        reasons.append("exchange_listing")
    if lead.source.startswith("telegram:"):
        score += 20
        reasons.append("mining_release")
    if lead.source.startswith("rss:"):
        score += 6
        reasons.append("rss_feed")
    if lead.source in ("yiimp_pools",) or lead.source in ("zpool", "zergpool", "rplant"):
        score += 18
        reasons.append("pool_api")
    if lead.source.startswith("yiimp") or "yiimp" in lead.tags:
        score += 15
        reasons.append("yiimp_pool")
    if lead.source == "rainbowminer":
        score += 14
        reasons.append("rainbowminer_db")
    if lead.source == "coinpaprika":
        score += 8
        reasons.append("aggregator_new")
    if lead.source == "github_release":
        score += 12
        reasons.append("github_release")
    if lead.source == "nicehash":
        score += 10
        reasons.append("nicehash_algo")
    if lead.source.startswith("exchange:"):
        score += 10
        reasons.append("small_exchange")

    # URL hints
    url_l = lead.url.lower()
    if "github.com" in url_l:
        score += 5
    if "bitcointalk.org" in url_l:
        score += 3

    lead.score = max(score, 0)
    lead.score_reasons = reasons[:12]
    return lead
