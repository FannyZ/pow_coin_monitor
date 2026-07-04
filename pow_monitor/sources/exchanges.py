from __future__ import annotations

import logging

from pow_monitor.baseline import SourceBaseline
from pow_monitor.config import ROOT
from pow_monitor.models import CoinLead, now_iso
from pow_monitor.sources.base import FetchError, http_get_json

logger = logging.getLogger(__name__)


def _parse_xeggex(data: dict) -> list[tuple[str, str]]:
    markets = data if isinstance(data, list) else data.get("data") or data.get("markets") or []
    out: list[tuple[str, str]] = []
    for m in markets:
        if not isinstance(m, dict):
            continue
        symbol = str(m.get("symbol") or m.get("market") or "")
        base = str(m.get("base") or m.get("baseCurrency") or symbol.split("-")[0] if symbol else "")
        if symbol:
            out.append((symbol, base))
    return out


def fetch_exchanges(source_cfg: dict, monitor_cfg: dict) -> list[CoinLead]:
    exchanges = source_cfg.get("exchanges", [])
    max_per = int(source_cfg.get("max_per_exchange", 20))
    baseline = SourceBaseline(ROOT / source_cfg.get("baseline_path", "data/exchanges_baseline.json"))
    leads: list[CoinLead] = []

    for ex in exchanges:
        if not ex.get("enabled", True):
            continue
        name = ex.get("name", "exchange")
        url = ex["url"]
        ex_type = ex.get("type", "generic")

        try:
            data = http_get_json(url, monitor_cfg, referer=ex.get("referer"))
        except FetchError as exc:
            logger.warning("Exchange %s fetch failed: %s", name, exc)
            continue

        symbols: list[str] = []
        meta: dict[str, str] = {}
        if ex_type == "xeggex":
            for symbol, base in _parse_xeggex(data):
                symbols.append(symbol)
                meta[symbol] = base
        elif ex_type == "tradeogre":
            if isinstance(data, dict):
                symbols = list(data.keys())
        else:
            if isinstance(data, list):
                symbols = [str(x) for x in data]
            elif isinstance(data, dict):
                symbols = list(data.keys())

        new_symbols = baseline.filter_new(name, symbols)
        count = 0
        for symbol in sorted(new_symbols)[:max_per]:
            base = meta.get(symbol, symbol.split("-")[0] if "-" in symbol else symbol)
            leads.append(
                CoinLead(
                    source=f"exchange:{name}",
                    title=f"{base} — new market on {name}",
                    url=ex.get("web_url", url),
                    summary=f"New trading pair/market detected: {symbol}",
                    tags=[base.lower(), name, "exchange"],
                    discovered_at=now_iso(),
                    extra={"symbol": symbol, "exchange": name},
                )
            )
            count += 1

        logger.info("Exchange %s: %d markets tracked, %d new", name, len(symbols), count)

    return leads
