from __future__ import annotations

from typing import Any


def _esc_md(value: str | None) -> str:
    if not value:
        return ""
    return (
        str(value)
        .replace("_", "\\_")
        .replace("*", "\\*")
        .replace("[", "\\[")
        .replace("`", "\\`")
    )


def _esc(value: str | None) -> str:
    return _esc_md(value)


def _link_line(label: str, url: str) -> str:
    url = str(url or "").strip()
    if not url:
        return ""
    return f"{_esc_md(label)}: {url}"


def _wallet_explorer_url(explorer: str, wallet: str) -> str:
    base = str(explorer or "").strip().rstrip("/")
    address = str(wallet or "").strip()
    if not base or not address:
        return ""
    if address.startswith("http://") or address.startswith("https://"):
        return address
    if "/address/" in base or "/account/" in base:
        return base
    return f"{base}/address/{address}"


def _infer_github(source: str, url: str, extra: dict[str, Any]) -> str:
    github = str(extra.get("github") or "").strip()
    if github:
        return github
    if url.startswith("https://github.com/") or url.startswith("http://github.com/"):
        return url
    if source in ("github", "github_release") or source.startswith("github"):
        return url if "github.com" in url else ""
    repo = str(extra.get("repo") or "").strip()
    if repo and "/" in repo:
        return f"https://github.com/{repo.strip('/')}"
    return ""


def _collect_links(facts: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    if facts.get("website"):
        lines.append(_link_line("官网", str(facts["website"])))
    if facts.get("github") and facts["github"] != facts.get("website"):
        lines.append(_link_line("GitHub", str(facts["github"])))
    if facts.get("explorer"):
        lines.append(_link_line("浏览器", str(facts["explorer"])))
    if facts.get("rpc"):
        lines.append(_link_line("RPC", str(facts["rpc"])))
    if facts.get("pool_link"):
        lines.append(_link_line("矿池", str(facts["pool_link"])))
    elif facts.get("pool_line"):
        lines.append(f"矿池: {_esc_md(str(facts['pool_line']))}")
    if facts.get("exchange_link"):
        lines.append(_link_line("交易所", str(facts["exchange_link"])))
    wallet = str(facts.get("wallet") or "").strip()
    if wallet:
        wallet_url = _wallet_explorer_url(str(facts.get("explorer") or ""), wallet)
        if wallet_url:
            lines.append(_link_line("钱包", wallet_url))
        else:
            lines.append(f"钱包: {_esc_md(_short_addr(wallet))}")
    if facts.get("announcement"):
        lines.append(_link_line("公告", str(facts["announcement"])))
    primary = str(facts.get("primary_link") or "").strip()
    if primary:
        lines.append(_link_line("详情", primary))
    return [line for line in lines if line]


def _short_text(value: str, limit: int = 60) -> str:
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _short_addr(value: str) -> str:
    text = str(value).strip()
    if len(text) <= 22:
        return text
    return f"{text[:10]}…{text[-8:]}"


def extract_coin_facts(coin: dict[str, Any]) -> dict[str, Any]:
    extra = coin.get("extra") or {}
    source = str(coin.get("source") or "")
    url = str(coin.get("url") or "")
    pool_name = extra.get("pool")
    port = extra.get("port")
    pool_line = ""
    pool_link = ""
    if pool_name and port:
        pool_line = f"{pool_name}:{port}"
    elif pool_name and not str(pool_name).endswith("/api/currencies"):
        pool_line = str(pool_name)

    pool_url = str(extra.get("pool_url") or "")
    if pool_url and "/api/" not in pool_url:
        pool_link = pool_url

    website = str(extra.get("website") or extra.get("site") or extra.get("homepage") or "").strip()
    github = _infer_github(source, url, extra)
    explorer = str(extra.get("explorer") or "").strip()
    rpc = str(extra.get("rpc") or "").strip()
    exchange_link = str(extra.get("website") or "").strip() if source.startswith("exchange:") else ""
    if not exchange_link:
        exchange_link = str(extra.get("web_url") or "").strip()

    announcement = url if source.startswith("telegram:") else ""
    primary_link = ""
    if url and url != github and url != website and url != announcement:
        primary_link = url
    elif source.startswith("exchange:") and url:
        primary_link = url

    return {
        "title": coin.get("title", ""),
        "score": coin.get("score", 0),
        "source": source,
        "algo": extra.get("algo") or extra.get("algorithm") or "",
        "ticker": extra.get("ticker") or "",
        "website": website,
        "github": github,
        "explorer": explorer,
        "rpc": rpc,
        "pool_link": pool_link,
        "pool_line": pool_line,
        "wallet": extra.get("wallet") or "",
        "exchange_link": exchange_link,
        "announcement": announcement,
        "primary_link": primary_link,
        "summary": coin.get("summary") or "",
        "reasons": coin.get("score_reasons") or [],
    }


def format_coin_lines(coin: dict[str, Any], index: int) -> list[str]:
    facts = extract_coin_facts(coin)
    lines = [f"*{index}. {_esc(facts['title'][:80])}*"]

    meta = [f"分数: {facts['score']}", f"来源: {_esc(facts['source'])}"]
    if facts["algo"]:
        meta.append(f"算法: {_esc(str(facts['algo']))}")
    if facts["ticker"] and facts["ticker"] not in facts["title"]:
        meta.append(f"代号: {_esc(str(facts['ticker']))}")
    lines.append(" | ".join(meta))

    link_lines = _collect_links(facts)
    if link_lines:
        lines.extend(link_lines)
    else:
        fallback = str(coin.get("url") or "").strip()
        if fallback:
            lines.append(_link_line("链接", fallback))

    if facts["summary"]:
        lines.append(f"摘要: {_esc(_short_text(facts['summary'], 80))}")

    if facts["reasons"]:
        lines.append(f"命中: {_esc(', '.join(facts['reasons'][:4]))}")

    return lines


def format_coin_alert(coins: list[dict[str, Any]], scan_meta: dict[str, Any]) -> str:
    lines = [
        "*⛏ PoW 新币监控*",
        f"扫描时间 UTC: {_esc(scan_meta.get('finished_at', ''))}",
        f"来源: {_esc(', '.join(scan_meta.get('sources_ok', [])))}",
        f"新发现 *{scan_meta.get('new_count', 0)}* 条 | 总计 {_esc(str(scan_meta.get('total_leads', 0)))} 条",
        "",
    ]

    for i, coin in enumerate(coins[:8], 1):
        lines.extend(format_coin_lines(coin, i))
        lines.append("")

    lines.append("_请自行验证官网/GitHub/矿池/钱包地址，谨防诈骗。_")
    return "\n".join(lines)


def format_daily_report(scan: dict[str, Any], learning: dict[str, Any] | None = None) -> str:
    learning = learning or {}
    notify_min = int(scan.get("notify_min_score", 40))
    candidates = scan.get("notify_candidates") or [
        lead for lead in scan.get("new_leads", []) if lead.get("score", 0) >= notify_min
    ]

    lines = [
        "*⛏ PoW 新币监控 — 每日报告*",
        "",
        "*扫描结果*",
        f"- 时间 UTC: {_esc(scan.get('finished_at', ''))}",
        (
            f"- 新发现: {scan.get('new_count', 0)} | 合格: {scan.get('total_leads', 0)}"
            f" | 自动推送: {'是' if scan.get('telegram_sent') else '否'}"
        ),
        "",
        f"*新高分新币（≥{notify_min}）*",
    ]

    if candidates:
        for i, coin in enumerate(candidates[:8], 1):
            lines.extend(format_coin_lines(coin, i))
            lines.append("")
    else:
        lines.append("无新高分新币")
        lines.append("")

    lines.extend(
        [
            "*今日自学习*",
            f"- 互联网搜索次数: {learning.get('searches', 0)}",
        ]
    )

    added = learning.get("sources_added") or []
    if added:
        lines.append(f"- 新发现来源: {len(added)} 个")
        for item in added[:5]:
            if isinstance(item, dict):
                lines.append(f"  · {_esc(item.get('name', ''))} {_esc(item.get('url', ''))}")
            else:
                lines.append(f"  · {_esc(str(item))}")
    else:
        lines.append("- 新发现来源: 0 个")

    lines.extend(
        [
            f"- 已写入 discovered_sources.yaml: {learning.get('discovered_written', 0)} 个",
            f"- 已 push GitHub: {'是' if learning.get('pushed') else '否'}",
        ]
    )

    pending = learning.get("pending_urls") or []
    if pending:
        lines.append(f"- 文档未接入待办: {_esc(', '.join(str(x) for x in pending[:3]))}")

    ok = ", ".join(scan.get("sources_ok", []))
    empty = ", ".join(scan.get("sources_empty", [])) or "无"
    failed = ", ".join(scan.get("sources_failed", [])) or "无"
    lines.extend(
        [
            "",
            "*来源状态*",
            f"正常: {_esc(ok)}",
            f"无新结果: {_esc(empty)}",
            f"失败: {_esc(failed)}",
            "",
            "_请自行验证官网/GitHub/矿池/钱包地址，谨防诈骗。_",
        ]
    )
    return "\n".join(lines)
