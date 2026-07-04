#!/usr/bin/env python3
"""Validate URLs in config/discovered_sources.yaml (smoke test)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import requests
import yaml

from pow_monitor.config import load_config


def _check_url(url: str, timeout: int = 15) -> tuple[bool, str]:
    try:
        r = requests.get(
            url,
            headers={"User-Agent": "PowCoinMonitor/2.0"},
            timeout=timeout,
            allow_redirects=True,
        )
        if r.status_code < 400:
            return True, f"HTTP {r.status_code}"
        return False, f"HTTP {r.status_code}"
    except Exception as exc:
        return False, str(exc)[:120]


def main() -> int:
    cfg = load_config()
    ok = 0
    fail = 0

    checks: list[tuple[str, str]] = []
    sources = cfg.sources

    for feed in sources.get("rss_feeds", {}).get("feeds", []):
        checks.append((f"rss:{feed.get('name')}", feed.get("url", "")))
    for pool in sources.get("yiimp_pools", {}).get("pools", []):
        checks.append((f"pool:{pool.get('name')}", pool.get("url", "")))
    for ep in sources.get("generic_json", {}).get("endpoints", []):
        checks.append((f"json:{ep.get('name')}", ep.get("url", "")))
    for ex in sources.get("exchanges", {}).get("exchanges", []):
        checks.append((f"exchange:{ex.get('name')}", ex.get("url", "")))

    for name, url in checks:
        if not url:
            continue
        good, msg = _check_url(url)
        status = "OK" if good else "FAIL"
        print(f"[{status}] {name}: {msg} — {url[:80]}")
        if good:
            ok += 1
        else:
            fail += 1

    print(f"\nValidated: {ok} ok, {fail} failed")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
