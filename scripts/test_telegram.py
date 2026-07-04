#!/usr/bin/env python3
"""Test Telegram connectivity (same env vars as btc_trend_monitor)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pow_monitor.config import load_config
from pow_monitor.notify.telegram import send_telegram_message


def main() -> int:
    cfg = load_config()
    if not cfg.telegram_bot_token or not cfg.telegram_chat_id:
        print("请在 .env 中配置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID")
        return 1
    ok = send_telegram_message(
        cfg.telegram_bot_token,
        cfg.telegram_chat_id,
        "*PoW Coin Monitor* 测试消息\nTelegram 配置正常 ✅",
    )
    print("发送成功" if ok else "发送失败")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
