from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class AppConfig:
    raw: dict[str, Any]
    monitor: dict[str, Any]
    sources: dict[str, Any]
    keywords: dict[str, Any]
    telegram: dict[str, Any]
    logging: dict[str, Any]
    storage: dict[str, Any]
    telegram_bot_token: str
    telegram_chat_id: str


def load_config(path: Path | None = None) -> AppConfig:
    load_dotenv(ROOT / ".env")
    cfg_path = path or ROOT / "config.yaml"
    with open(cfg_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return AppConfig(
        raw=raw,
        monitor=raw.get("monitor", {}),
        sources=raw.get("sources", {}),
        keywords=raw.get("keywords", {}),
        telegram=raw.get("telegram", {}),
        logging=raw.get("logging", {}),
        storage=raw.get("storage", {}),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
    )
