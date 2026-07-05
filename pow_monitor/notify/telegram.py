from __future__ import annotations

import logging
from typing import Any

import requests

from pow_monitor.notify.formatting import format_coin_alert, format_daily_report

logger = logging.getLogger(__name__)

__all__ = ["send_telegram_message", "format_coin_alert", "format_daily_report"]


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
