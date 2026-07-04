from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pow_monitor.config import ROOT, AppConfig

logger = logging.getLogger(__name__)

SOURCE_DOC = ROOT / "docs" / "DISCOVERY_SOURCES.md"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _walk_endpoints(sources: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    def add(source_type: str, name: str, url: str, extra: dict[str, Any] | None = None) -> None:
        if not url:
            return
        items.append(
            {
                "source_type": source_type,
                "name": name,
                "url": url,
                **(extra or {}),
            }
        )

    for src_name, cfg in sources.items():
        if not isinstance(cfg, dict) or not cfg.get("enabled", True):
            continue

        if src_name == "bitcointalk":
            add("bitcointalk", "announcements", cfg.get("url", ""))
        elif src_name == "github":
            for q in cfg.get("queries", []):
                add("github_search", q[:60], f"https://api.github.com/search/repositories?q={q}")
        elif src_name == "miningpoolstats":
            add("miningpoolstats", "sitemap", cfg.get("sitemap_url", ""))
        elif src_name == "whattomine":
            add("whattomine", "coins", cfg.get("url", ""))
        elif src_name == "safetrade":
            add("safetrade", "home", cfg.get("url", ""))
        elif src_name == "coingecko":
            for q in cfg.get("search_queries", []):
                add("coingecko_search", q, f"https://api.coingecko.com/api/v3/search?query={q}")
        elif src_name == "coinpaprika":
            add("coinpaprika", "coins", cfg.get("url", ""))
        elif src_name == "rainbowminer":
            add("rainbowminer", "coinsdb", cfg.get("url", ""))
        elif src_name == "nicehash":
            add("nicehash", "algorithms", cfg.get("url", ""))
        elif src_name == "rss_feeds":
            for feed in cfg.get("feeds", []):
                if feed.get("enabled", True):
                    add("rss", feed.get("name", ""), feed.get("url", ""))
        elif src_name == "yiimp_pools":
            for pool in cfg.get("pools", []):
                if pool.get("enabled", True):
                    add("yiimp_pool", pool.get("name", ""), pool.get("url", ""))
        elif src_name == "telegram_public":
            for ch in cfg.get("channels", []):
                if ch.get("enabled", True):
                    slug = ch.get("slug", "")
                    add("telegram", ch.get("name", slug), ch.get("url") or f"https://t.me/s/{slug}")
        elif src_name == "exchanges":
            for ex in cfg.get("exchanges", []):
                if ex.get("enabled", True):
                    add("exchange", ex.get("name", ""), ex.get("url", ""))
        elif src_name == "github_releases":
            for repo in cfg.get("repos", []):
                if repo.get("enabled", True):
                    slug = repo.get("repo", "")
                    add("github_release", repo.get("label", slug), f"https://github.com/{slug}/releases.atom")
        elif src_name == "generic_json":
            for ep in cfg.get("endpoints", []):
                if ep.get("enabled", True):
                    add("generic_json", ep.get("name", ""), ep.get("url", ""), {"mode": ep.get("mode", "dict_keys")})

    return items


def _urls_from_docs() -> list[str]:
    if not SOURCE_DOC.exists():
        return []
    text = SOURCE_DOC.read_text(encoding="utf-8")
    urls = re.findall(r"https?://[^\s\)>\"']+", text)
    skip = ("127.0.0.1", "localhost", "example.com")
    return sorted({u for u in urls if not any(s in u for s in skip)})


def build_inventory(cfg: AppConfig) -> dict[str, Any]:
    endpoints = _walk_endpoints(cfg.sources)
    doc_urls = _urls_from_docs()
    active_urls = {e["url"] for e in endpoints}

    return {
        "generated_at": _now_iso(),
        "active_source_modules": sorted(cfg.sources.keys()),
        "active_endpoints_count": len(endpoints),
        "active_endpoints": endpoints,
        "documented_urls_count": len(doc_urls),
        "documented_urls_not_in_config": [u for u in doc_urls if u not in active_urls][:50],
        "discovered_sources_path": cfg.discovery.get("discovered_sources_path", "config/discovered_sources.yaml"),
    }


def write_inventory(cfg: AppConfig) -> Path:
    inv = build_inventory(cfg)
    json_path = ROOT / "data" / "source_inventory.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(inv, ensure_ascii=False, indent=2), encoding="utf-8")

    md_path = ROOT / cfg.discovery.get("inventory_md_path", "docs/SOURCE_INVENTORY.md")
    lines = [
        "# 当前监控资源清单（自动生成）",
        "",
        f"生成时间 UTC: {inv['generated_at']}",
        "",
        f"- 活跃来源模块: **{len(inv['active_source_modules'])}**",
        f"- 活跃端点: **{inv['active_endpoints_count']}**",
        f"- 文档中未接入 URL（待评估）: **{len(inv['documented_urls_not_in_config'])}**",
        "",
        "## 活跃端点",
        "",
        "| 类型 | 名称 | URL |",
        "|------|------|-----|",
    ]
    for ep in inv["active_endpoints"]:
        url = ep["url"].replace("|", "\\|")
        lines.append(f"| {ep['source_type']} | {ep.get('name', '')} | {url} |")

    if inv["documented_urls_not_in_config"]:
        lines.extend(["", "## 文档有、代码未接入（Agent 优先补全）", ""])
        for url in inv["documented_urls_not_in_config"][:30]:
            lines.append(f"- {url}")

    lines.extend(
        [
            "",
            "## Agent 如何追加新来源",
            "",
            "1. 验证 URL 可访问（HTTP 200 / 有效 RSS / JSON）",
            "2. 写入 `config/discovered_sources.yaml` 对应列表",
            "3. 运行 `./run.sh --dry-run` 验证",
            "4. `git commit` + `git push`",
            "",
            "无需改 Python 的类型：RSS、YiiMP 矿池 API、Telegram 频道、交易所 API、GitHub query/release、generic_json",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Wrote inventory: %s (%d endpoints)", md_path, inv["active_endpoints_count"])
    return md_path


def append_learning_log(event: dict[str, Any]) -> None:
    path = ROOT / "data" / "learning_log.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {"ts": _now_iso(), **event}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
