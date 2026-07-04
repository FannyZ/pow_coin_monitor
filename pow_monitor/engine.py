from __future__ import annotations

import logging
from typing import Any

from pow_monitor.config import AppConfig, ROOT
from pow_monitor.models import CoinLead, now_iso
from pow_monitor.notify.telegram import format_coin_alert, send_telegram_message
from pow_monitor.scoring import score_lead
from pow_monitor.sources import (
    fetch_bitcointalk,
    fetch_coingecko,
    fetch_coinpaprika,
    fetch_exchanges,
    fetch_github,
    fetch_github_releases,
    fetch_miningpoolstats,
    fetch_nicehash,
    fetch_rainbowminer,
    fetch_rss_feeds,
    fetch_safetrade,
    fetch_telegram_public,
    fetch_whattomine,
    fetch_yiimp_pools,
)
from pow_monitor.store import CoinStore

logger = logging.getLogger(__name__)


def _collect_leads(cfg: AppConfig) -> tuple[list[CoinLead], list[str], list[str], list[str]]:
    monitor = cfg.monitor
    sources = cfg.sources
    all_leads: list[CoinLead] = []
    ok: list[str] = []
    failed: list[str] = []
    empty: list[str] = []

    fetchers = [
        ("telegram_public", fetch_telegram_public),
        ("yiimp_pools", fetch_yiimp_pools),
        ("rss_feeds", fetch_rss_feeds),
        ("rainbowminer", fetch_rainbowminer),
        ("coinpaprika", fetch_coinpaprika),
        ("github_releases", fetch_github_releases),
        ("exchanges", fetch_exchanges),
        ("nicehash", fetch_nicehash),
        ("bitcointalk", fetch_bitcointalk),
        ("github", fetch_github),
        ("miningpoolstats", fetch_miningpoolstats),
        ("whattomine", fetch_whattomine),
        ("safetrade", fetch_safetrade),
        ("coingecko", fetch_coingecko),
    ]

    for name, fn in fetchers:
        sc = sources.get(name, {})
        if not sc.get("enabled", True):
            continue
        try:
            leads = fn(sc, monitor)
            all_leads.extend(leads)
            ok.append(name)
            if not leads:
                empty.append(name)
                logger.warning("Source %s returned 0 leads (network block or no new items)", name)
        except Exception as exc:
            logger.exception("Source %s failed: %s", name, exc)
            failed.append(name)

    return all_leads, ok, failed, empty


def _dedupe_leads(leads: list[CoinLead]) -> list[CoinLead]:
    by_fp: dict[str, CoinLead] = {}
    for lead in leads:
        fp = lead.fingerprint
        if fp not in by_fp or lead.score > by_fp[fp].score:
            by_fp[fp] = lead
    return list(by_fp.values())


def run_scan(cfg: AppConfig, *, dry_run: bool = False, send_telegram: bool = True) -> dict[str, Any]:
    started = now_iso()
    min_score = int(cfg.monitor.get("min_score", 25))
    notify_min = int(cfg.monitor.get("notify_min_score", 40))

    raw_leads, sources_ok, sources_failed, sources_empty = _collect_leads(cfg)

    scored: list[CoinLead] = []
    for lead in raw_leads:
        scored.append(score_lead(lead, cfg.keywords))

    scored = [l for l in scored if l.score >= min_score]
    scored.sort(key=lambda x: x.score, reverse=True)
    scored = _dedupe_leads(scored)

    db_path = ROOT / cfg.storage.get("db_path", "data/coins.db")
    store = CoinStore(db_path)

    new_leads: list[dict[str, Any]] = []
    for lead in scored:
        d = lead.to_dict()
        is_new = store.upsert_lead(d, now_iso())
        if is_new:
            new_leads.append(d)

    finished = now_iso()
    meta = {
        "started_at": started,
        "finished_at": finished,
        "sources_ok": sources_ok,
        "sources_failed": sources_failed,
        "sources_empty": sources_empty,
        "total_leads": len(scored),
        "new_count": len(new_leads),
        "min_score": min_score,
        "notify_min_score": notify_min,
    }
    store.record_scan(started, finished, len(scored), len(new_leads), meta)

    notify_candidates = [l for l in new_leads if l.get("score", 0) >= notify_min]
    telegram_sent = False

    if (
        send_telegram
        and not dry_run
        and cfg.telegram.get("enabled", True)
        and notify_candidates
    ):
        max_per = int(cfg.telegram.get("max_coins_per_message", 8))
        text = format_coin_alert(notify_candidates[:max_per], meta)
        telegram_sent = send_telegram_message(
            cfg.telegram_bot_token,
            cfg.telegram_chat_id,
            text,
        )
        if telegram_sent:
            store.mark_notified([c["fingerprint"] for c in notify_candidates[:max_per]])

    report = {
        **meta,
        "dry_run": dry_run,
        "telegram_sent": telegram_sent,
        "top_leads": [l.to_dict() for l in scored[:20]],
        "new_leads": new_leads[:20],
        "notify_candidates": notify_candidates[:10],
    }
    return report
