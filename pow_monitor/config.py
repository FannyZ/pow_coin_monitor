from __future__ import annotations

import copy
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent

LIST_MERGE_FIELDS = ("feeds", "pools", "channels", "exchanges", "queries", "repos", "endpoints", "search_queries")


@dataclass
class AppConfig:
    raw: dict[str, Any]
    monitor: dict[str, Any]
    sources: dict[str, Any]
    keywords: dict[str, Any]
    telegram: dict[str, Any]
    logging: dict[str, Any]
    storage: dict[str, Any]
    discovery: dict[str, Any]
    telegram_bot_token: str
    telegram_chat_id: str


def _merge_list_items(base: list[Any], extra: list[Any]) -> list[Any]:
    merged = list(base)
    seen: set[str] = set()
    for item in base:
        if isinstance(item, dict):
            seen.add(str(item.get("name") or item.get("url") or item.get("repo") or item.get("slug") or ""))
        else:
            seen.add(str(item))
    for item in extra:
        if isinstance(item, dict):
            key = str(item.get("name") or item.get("url") or item.get("repo") or item.get("slug") or "")
        else:
            key = str(item)
        if not key or key in seen:
            continue
        merged.append(item)
        seen.add(key)
    return merged


def merge_discovered_sources(sources: dict[str, Any], discovered: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(sources)
    disc_sources = discovered.get("sources", discovered)
    if not isinstance(disc_sources, dict):
        return out

    for name, disc_cfg in disc_sources.items():
        if not isinstance(disc_cfg, dict):
            continue
        if name not in out:
            out[name] = copy.deepcopy(disc_cfg)
            continue
        base_cfg = out[name]
        for field in LIST_MERGE_FIELDS:
            if field not in disc_cfg:
                continue
            base_list = base_cfg.get(field, [])
            extra_list = disc_cfg.get(field, [])
            if isinstance(base_list, list) and isinstance(extra_list, list):
                base_cfg[field] = _merge_list_items(base_list, extra_list)
        if disc_cfg.get("enabled") is not None and "enabled" not in base_cfg:
            base_cfg["enabled"] = disc_cfg["enabled"]
    return out


def load_config(path: Path | None = None) -> AppConfig:
    load_dotenv(ROOT / ".env", override=True)
    cfg_path = path or ROOT / "config.yaml"
    with open(cfg_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    discovery = raw.get("discovery", {})
    disc_path = ROOT / discovery.get("discovered_sources_path", "config/discovered_sources.yaml")
    sources = raw.get("sources", {})
    if disc_path.exists():
        with open(disc_path, encoding="utf-8") as f:
            discovered = yaml.safe_load(f) or {}
        sources = merge_discovered_sources(sources, discovered)

    return AppConfig(
        raw=raw,
        monitor=raw.get("monitor", {}),
        sources=sources,
        keywords=raw.get("keywords", {}),
        telegram=raw.get("telegram", {}),
        logging=raw.get("logging", {}),
        storage=raw.get("storage", {}),
        discovery=discovery,
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
    )
