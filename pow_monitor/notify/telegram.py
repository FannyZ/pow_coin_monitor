from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


def send_telegram_message(token: str, chat_id: str, text: str, parse_mode: str = "Markdown") -> bool:
    if not token or not chat_id:
        logger.warning("Telegram not configured; skipping notification")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text[:4096],
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            },
            timeout=20,
        )
        data = resp.json()
        if not data.get("ok"):
            logger.error("Telegram API error: %s", data)
            return False
        return True
    except Exception as exc:
        logger.error("Telegram send failed: %s", exc)
        return False


def _esc(value: str | None) -> str:
    if not value:
        return ""
    return (
        str(value)
        .replace("_", "\\_")
        .replace("*", "\\*")
        .replace("[", "\\[")
        .replace("`", "\\`")
    )


def format_coin_alert(coins: list[dict[str, Any]], scan_meta: dict[str, Any]) -> str:
    lines = [
        "*⛏ PoW 新币监控*",
        f"扫描时间 UTC: {_esc(scan_meta.get('finished_at', ''))}",
        f"来源: {_esc(', '.join(scan_meta.get('sources_ok', [])))}",
        f"新发现 *{scan_meta.get('new_count', 0)}* 条 | 总计 {_esc(str(scan_meta.get('total_leads', 0)))} 条",
        "",
    ]

    for i, c in enumerate(coins[:8], 1):
        lines.extend(
            [
                f"*{i}. {_esc(c.get('title', '')[:80])}*",
                f"分数: {c.get('score', 0)} | 来源: {_esc(c.get('source', ''))}",
                f"{_esc(c.get('url', ''))}",
            ]
        )
        reasons = c.get("score_reasons") or []
        if reasons:
            lines.append(f"命中: {_esc(', '.join(reasons[:5]))}")
        lines.append("")

    lines.append("_请自行验证官网/GitHub/矿池，谨防诈骗。_")
    return "\n".join(lines)
