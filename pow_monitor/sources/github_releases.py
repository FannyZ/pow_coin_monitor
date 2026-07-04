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


def fetch_github_releases(source_cfg: dict, monitor_cfg: dict) -> list[CoinLead]:
    repos = source_cfg.get("repos", [])
    max_per_repo = int(source_cfg.get("max_per_repo", 3))
    baseline = SourceBaseline(ROOT / source_cfg.get("baseline_path", "data/github_releases_baseline.json"))
    leads: list[CoinLead] = []

    for repo in repos:
        if not repo.get("enabled", True):
            continue
        slug = repo["repo"]
        label = repo.get("label", slug)
        atom_url = repo.get("atom_url") or f"https://github.com/{slug}/releases.atom"

        try:
            xml = http_get(atom_url, monitor_cfg, referer=f"https://github.com/{slug}")
            root = ET.fromstring(xml)
        except (FetchError, ET.ParseError) as exc:
            logger.warning("GitHub releases %s failed: %s", slug, exc)
            continue

        entries = root.findall("a:entry", ATOM_NS)
        entry_ids = []
        for entry in entries[: max_per_repo * 2]:
            entry_id = entry.findtext("a:id", default="", namespaces=ATOM_NS)
            if entry_id:
                entry_ids.append(entry_id)

        new_ids = baseline.filter_new(slug, entry_ids)
        count = 0
        for entry in entries:
            entry_id = entry.findtext("a:id", default="", namespaces=ATOM_NS)
            if entry_id not in new_ids:
                continue
            title = unescape(entry.findtext("a:title", default="", namespaces=ATOM_NS) or "")
            link = ""
            for link_node in entry.findall("a:link", ATOM_NS):
                href = link_node.get("href")
                if href:
                    link = href
                    break
            summary = unescape(re.sub(r"<[^>]+>", " ", entry.findtext("a:summary", default="", namespaces=ATOM_NS) or ""))
            leads.append(
                CoinLead(
                    source="github_release",
                    title=f"{label}: {title[:120]}",
                    url=link or f"https://github.com/{slug}/releases",
                    summary=summary[:400],
                    tags=[slug.split("/")[-1].lower(), "github", "release"],
                    discovered_at=now_iso(),
                    extra={"repo": slug},
                )
            )
            count += 1
            if count >= max_per_repo:
                break

        logger.info("GitHub releases %s: %d new", slug, count)

    return leads
