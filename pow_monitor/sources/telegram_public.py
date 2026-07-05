from __future__ import annotations

import logging
import re
from html import unescape
from typing import Any

from pow_monitor.baseline import SourceBaseline
from pow_monitor.config import ROOT
from pow_monitor.models import CoinLead, now_iso
from pow_monitor.sources.base import FetchError, http_get

logger = logging.getLogger(__name__)

MSG_ID_RE = re.compile(r'data-post="miningrelease/(\d+)"')
COIN_LINE_RE = re.compile(
    r"Coin Name:\s*([^<\n]+?)\s*Ticker:\s*\$?([A-Z0-9]+)(?:\s*Algo:\s*([^<\n]+))?",
    re.I,
)
URL_RE = re.compile(r"https?://[^\s<>\"']+")
WALLET_PATTERNS = [
    re.compile(r"\b(0x[a-fA-F0-9]{40})\b"),
    re.compile(r"\b([13][a-km-zA-HJ-NP-Z1-9]{25,34})\b"),
    re.compile(r"\b(bc1[a-z0-9]{25,90})\b", re.I),
    re.compile(r"\b([LM][a-km-zA-HJ-NP-Z1-9]{26,33})\b"),
]
LABELED_FIELDS = [
    ("website", r"(?:website|site|官网)\s*:?\s*(\S+)"),
    ("explorer", r"(?:explorer|区块浏览器|block explorer url)\s*:?\s*(\S+)"),
    ("github", r"github\s*:?\s*(\S+)"),
    ("rpc", r"rpc url\s*:?\s*(\S+)"),
    ("pool", r"(?:pool|矿池|stratum)\s*:?\s*(\S+)"),
    ("wallet", r"(?:wallet|地址|address)\s*:?\s*(\S+)"),
    ("discord", r"discord\s*:?\s*(\S+)"),
    ("bitcointalk", r"(?:bitcointalk|ann)\s*:?\s*(\S+)"),
]
COIN_REF_RE = re.compile(r"for\s+([A-Za-z0-9][A-Za-z0-9 \-]+)", re.I)


def _strip_html(text: str) -> str:
    text = unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return " ".join(text.split())


def _clean_token(value: str) -> str:
    return value.strip().rstrip(".,;)")


def _classify_href(href: str) -> str | None:
    lower = href.lower()
    if "t.me/" in lower or "telegram." in lower:
        return None
    if "github.com/" in lower:
        return "github"
    if any(token in lower for token in ("explorer", "chainz", "cryptoid", "blockbook", "scan.", "blockchair")):
        return "explorer"
    return "website"


def _parse_mining_post(block: str) -> dict[str, Any]:
    text = _strip_html(block)
    extra: dict[str, Any] = {}

    coin_match = COIN_LINE_RE.search(text)
    if coin_match:
        extra["coin_name"] = coin_match.group(1).strip()
        extra["ticker"] = coin_match.group(2).strip()
        extra["algo"] = (coin_match.group(3) or "").strip()

    coin_ref = COIN_REF_RE.search(text)
    if coin_ref:
        extra["coin_ref"] = coin_ref.group(1).strip()

    for key, pattern in LABELED_FIELDS:
        match = re.search(pattern, text, re.I)
        if match:
            extra[key] = _clean_token(match.group(1))

    for href in re.findall(r'href="(https?://[^"]+)"', block):
        href = _clean_token(unescape(href))
        field = _classify_href(href)
        if field and not extra.get(field):
            extra[field] = href

    if not extra.get("wallet"):
        for pattern in WALLET_PATTERNS:
            match = pattern.search(text)
            if match:
                extra["wallet"] = match.group(1)
                break

    links = []
    for url in URL_RE.findall(text):
        url = _clean_token(url)
        if url not in links:
            links.append(url)
    if links:
        extra["links"] = links[:5]

    return extra


def _merge_supplements(leads: list[CoinLead], blocks: list[str]) -> None:
    if not leads:
        return

    by_name: dict[str, CoinLead] = {}
    for lead in leads:
        coin_name = str(lead.extra.get("coin_name") or lead.title.split("(")[0]).strip().lower()
        if coin_name:
            by_name[coin_name] = lead

    for block in blocks:
        if COIN_LINE_RE.search(_strip_html(block)):
            continue
        supplement = _parse_mining_post(block)
        if not supplement:
            continue

        coin_ref = str(supplement.pop("coin_ref", "") or "").strip().lower()
        target = by_name.get(coin_ref)
        if not target and coin_ref:
            for name, lead in by_name.items():
                if coin_ref in name or name in coin_ref:
                    target = lead
                    break
        if not target and len(leads) == 1:
            target = leads[0]
        if not target:
            continue

        for key, value in supplement.items():
            if key in ("links", "channel", "message_id", "ticker", "algo", "coin_name"):
                continue
            if value and not target.extra.get(key):
                target.extra[key] = value


def fetch_telegram_public(source_cfg: dict, monitor_cfg: dict) -> list[CoinLead]:
    channels = source_cfg.get("channels", [])
    max_per_channel = int(source_cfg.get("max_per_channel", 20))
    baseline = SourceBaseline(ROOT / source_cfg.get("baseline_path", "data/telegram_baseline.json"))
    leads: list[CoinLead] = []

    for channel in channels:
        if not channel.get("enabled", True):
            continue
        name = channel.get("name", "telegram")
        slug = channel["slug"]
        url = channel.get("url") or f"https://t.me/s/{slug}"

        try:
            html = http_get(url, monitor_cfg)
        except FetchError as exc:
            logger.warning("Telegram channel %s fetch failed: %s", name, exc)
            continue

        blocks = re.findall(
            r'class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
            html,
            re.S,
        )

        message_ids: list[str] = []
        parsed: list[tuple[str, dict[str, Any], str]] = []
        for block in blocks:
            msg_match = MSG_ID_RE.search(block)
            msg_id = msg_match.group(1) if msg_match else str(abs(hash(block)))
            text = _strip_html(block)
            post_extra = _parse_mining_post(block)
            coin_name = post_extra.get("coin_name", "")
            ticker = post_extra.get("ticker", "")
            algo = post_extra.get("algo", "")

            if coin_name or ticker:
                message_ids.append(msg_id)
                parsed.append((msg_id, post_extra, text))
            elif channel.get("include_all", False) and "‼" in text:
                message_ids.append(msg_id)
                parsed.append((msg_id, {}, text))

        new_ids = baseline.filter_new(name, message_ids)
        count = 0
        for msg_id, post_extra, text in parsed:
            if msg_id not in new_ids:
                continue

            coin_name = post_extra.get("coin_name") or text[:80]
            ticker = post_extra.get("ticker", "")
            algo = post_extra.get("algo", "")
            title = f"{coin_name} ({ticker}) — {algo}" if ticker else coin_name
            summary_bits = [algo, post_extra.get("pool", "")]
            summary = ", ".join(x for x in summary_bits if x) or f"Mining launch via @{slug}"

            extra = {
                "channel": slug,
                "message_id": msg_id,
                **post_extra,
            }

            leads.append(
                CoinLead(
                    source=f"telegram:{name}",
                    title=title[:200],
                    url=f"https://t.me/{slug}/{msg_id}",
                    summary=summary,
                    tags=[ticker.lower(), algo.lower(), "telegram", "mining-release"] if ticker else ["telegram"],
                    discovered_at=now_iso(),
                    extra=extra,
                )
            )
            count += 1
            if count >= max_per_channel:
                break

        _merge_supplements(leads, blocks)

        logger.info("Telegram %s: %d launch posts, %d new", name, len(parsed), count)

    return leads
