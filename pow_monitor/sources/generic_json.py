from __future__ import annotations

import logging
from typing import Any

from pow_monitor.baseline import SourceBaseline
from pow_monitor.config import ROOT
from pow_monitor.models import CoinLead, now_iso
from pow_monitor.sources.base import FetchError, http_get_json

logger = logging.getLogger(__name__)


def _field_value(item: dict, field: str) -> Any:
    node: Any = item
    for part in field.split("."):
        if not part:
            continue
        if isinstance(node, dict):
            node = node.get(part)
        else:
            return None
    return node


def _extract_ids(data: Any, mode: str, list_path: str, id_field: str) -> list[str]:
    if mode == "list" and isinstance(data, list):
        out: list[str] = []
        for item in data:
            if isinstance(item, dict):
                val = str(_field_value(item, id_field) or item.get("id") or item.get("symbol") or "")
                if val:
                    out.append(val)
            elif item is not None:
                out.append(str(item))
        return out

    if mode == "list_path" and isinstance(data, dict):
        node: Any = data
        for part in list_path.split("."):
            if not part:
                continue
            node = node.get(part) if isinstance(node, dict) else None
        if isinstance(node, list):
            return _extract_ids(node, "list", "", id_field)
        if isinstance(node, dict):
            return [str(k) for k in node.keys()]

    if isinstance(data, dict):
        return [str(k) for k in data.keys()]
    return []


def fetch_generic_json(source_cfg: dict, monitor_cfg: dict) -> list[CoinLead]:
    if not source_cfg.get("enabled", True):
        return []

    endpoints = source_cfg.get("endpoints", [])
    max_per = int(source_cfg.get("max_per_endpoint", 20))
    baseline = SourceBaseline(ROOT / source_cfg.get("baseline_path", "data/generic_json_baseline.json"))
    leads: list[CoinLead] = []

    for ep in endpoints:
        if not ep.get("enabled", True):
            continue
        name = ep.get("name", "endpoint")
        url = ep.get("url", "")
        if not url:
            continue

        try:
            data = http_get_json(url, monitor_cfg, referer=ep.get("referer"))
        except FetchError as exc:
            logger.warning("generic_json %s failed: %s", name, exc)
            continue

        mode = ep.get("mode", "dict_keys")
        list_path = ep.get("list_path", "")
        id_field = ep.get("id_field", "id")
        ids = _extract_ids(data, mode, list_path, id_field)
        new_ids = baseline.filter_new(name, ids)

        for item_id in sorted(new_ids)[:max_per]:
            title = ep.get("title_template", "{name} new on {source}").format(
                name=item_id,
                source=name,
                id=item_id,
            )
            item_url = ep.get("link_template", url).format(id=item_id, name=item_id)
            leads.append(
                CoinLead(
                    source=f"generic_json:{name}",
                    title=title[:200],
                    url=item_url,
                    summary=f"New entry on generic JSON source {name}",
                    tags=[name, "generic_json"],
                    discovered_at=now_iso(),
                    extra={"endpoint": name, "item_id": item_id},
                )
            )

        logger.info("generic_json %s: %d ids, %d new", name, len(ids), len(new_ids))

    return leads
