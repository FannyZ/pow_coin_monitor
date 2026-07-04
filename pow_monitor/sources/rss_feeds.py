from __future__ import annotations

import logging
import re
from html import unescape
from xml.etree import ElementTree as ET

from pow_monitor.baseline import SourceBaseline
from pow_monitor.config import ROOT
from pow_monitor.models import CoinLead, now_iso
from pow_monitor.sources.base import FetchError, http_get

logger = logging.getLogger(__name__)

ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}


def _strip_html(text: str) -> str:
    text = unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return " ".join(text.split())


def _entry_id(entry: ET.Element) -> str:
    for tag in ("id", "{http://www.w3.org/2005/Atom}id"):
        node = entry.find(tag) if tag.startswith("{") else entry.find(f"a:id", ATOM_NS)
        if node is not None and node.text:
            return node.text.strip()
    link = entry.find("a:link", ATOM_NS)
    if link is not None and link.get("href"):
        return link.get("href", "")
    title = entry.find("a:title", ATOM_NS)
    if title is not None and title.text:
        return title.text.strip()
    return ""


def _entry_title(entry: ET.Element) -> str:
    node = entry.find("a:title", ATOM_NS)
    return _strip_html(node.text if node is not None else "")


def _entry_link(entry: ET.Element) -> str:
    for link in entry.findall("a:link", ATOM_NS):
        href = link.get("href")
        if href:
            return href
    return ""


def _entry_summary(entry: ET.Element) -> str:
    for path in ("a:summary", "a:content"):
        node = entry.find(path, ATOM_NS)
        if node is not None and (node.text or "").strip():
            return _strip_html(node.text)
    return ""


def _matches_keywords(text: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    lower = text.lower()
    return any(k.lower() in lower for k in keywords)


def fetch_rss_feeds(source_cfg: dict, monitor_cfg: dict) -> list[CoinLead]:
    feeds = source_cfg.get("feeds", [])
    max_per_feed = int(source_cfg.get("max_per_feed", 15))
    baseline = SourceBaseline(ROOT / source_cfg.get("baseline_path", "data/rss_baseline.json"))
    leads: list[CoinLead] = []

    headers = {
        "User-Agent": monitor_cfg.get("user_agent", "PowCoinMonitor/1.0"),
        "Accept": "application/atom+xml, application/rss+xml, application/xml, text/xml, */*",
    }

    for feed in feeds:
        if not feed.get("enabled", True):
            continue
        name = feed.get("name", "rss")
        url = feed["url"]
        keywords = feed.get("keywords", [])
        try:
            xml = http_get(url, monitor_cfg)
            root = ET.fromstring(xml)
        except (FetchError, ET.ParseError) as exc:
            logger.warning("RSS feed %s failed: %s", name, exc)
            continue

        entries = root.findall("a:entry", ATOM_NS)
        if not entries:
            entries = root.findall("channel/item")  # RSS 2.0 fallback

        new_ids: set[str] = set()
        for entry in entries[: max_per_feed * 3]:
            if entry.tag.endswith("item"):
                title = _strip_html(entry.findtext("title") or "")
                link = entry.findtext("link") or ""
                summary = _strip_html(entry.findtext("description") or "")
                entry_id = entry.findtext("guid") or link or title
            else:
                title = _entry_title(entry)
                link = _entry_link(entry)
                summary = _entry_summary(entry)
                entry_id = _entry_id(entry)

            if not title or not link:
                continue
            text = f"{title} {summary}"
            if not _matches_keywords(text, keywords):
                continue
            fp = f"{name}|{entry_id}"
            new_ids.add(fp)

        unseen = baseline.filter_new(name, new_ids)
        count = 0
        for entry in entries:
            if entry.tag.endswith("item"):
                title = _strip_html(entry.findtext("title") or "")
                link = entry.findtext("link") or ""
                summary = _strip_html(entry.findtext("description") or "")
                entry_id = entry.findtext("guid") or link or title
            else:
                title = _entry_title(entry)
                link = _entry_link(entry)
                summary = _entry_summary(entry)
                entry_id = _entry_id(entry)

            fp = f"{name}|{entry_id}"
            if fp not in unseen:
                continue
            text = f"{title} {summary}"
            if not _matches_keywords(text, keywords):
                continue

            leads.append(
                CoinLead(
                    source=f"rss:{name}",
                    title=title[:200],
                    url=link,
                    summary=summary[:500],
                    tags=[name, "rss"],
                    discovered_at=now_iso(),
                    extra={"feed": name},
                )
            )
            count += 1
            if count >= max_per_feed:
                break

        logger.info("RSS %s: %d new entries", name, count)

    return leads
