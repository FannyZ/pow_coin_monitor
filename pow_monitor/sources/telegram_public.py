from __future__ import annotations

import logging
import re
from html import unescape

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


def _strip_html(text: str) -> str:
    text = unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return " ".join(text.split())


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
        parsed: list[tuple[str, str, str, str]] = []
        for block in blocks:
            msg_match = MSG_ID_RE.search(block)
            msg_id = msg_match.group(1) if msg_match else str(abs(hash(block)))
            text = _strip_html(block)
            coin_match = COIN_LINE_RE.search(text)
            if coin_match:
                coin_name, ticker, algo = coin_match.groups()
                algo = (algo or "").strip()
                message_ids.append(msg_id)
                parsed.append((msg_id, coin_name.strip(), ticker.strip(), algo))
            elif channel.get("include_all", False) and "‼" in text:
                message_ids.append(msg_id)
                parsed.append((msg_id, text[:80], "", ""))

        new_ids = baseline.filter_new(name, message_ids)
        count = 0
        for msg_id, coin_name, ticker, algo in parsed:
            if msg_id not in new_ids:
                continue
            title = f"{coin_name} ({ticker}) — {algo}" if ticker else coin_name
            leads.append(
                CoinLead(
                    source=f"telegram:{name}",
                    title=title[:200],
                    url=f"https://t.me/{slug}/{msg_id}",
                    summary=f"Mining launch announcement via @{slug}: {algo or coin_name}",
                    tags=[ticker.lower(), algo.lower(), "telegram", "mining-release"] if ticker else ["telegram"],
                    discovered_at=now_iso(),
                    extra={"channel": slug, "message_id": msg_id, "ticker": ticker, "algo": algo},
                )
            )
            count += 1
            if count >= max_per_channel:
                break

        logger.info("Telegram %s: %d launch posts, %d new", name, len(parsed), count)

    return leads
