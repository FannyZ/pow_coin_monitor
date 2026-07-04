#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from pow_monitor.config import ROOT as PROJECT_ROOT, load_config
from pow_monitor.engine import run_scan
from pow_monitor.inventory import build_inventory, write_inventory


def setup_logging(level: str = "INFO") -> None:
    log_dir = PROJECT_ROOT / "data"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "monitor.log", encoding="utf-8"),
        ],
    )


def _print_report(report: dict) -> None:
    print("=" * 72)
    print(f"PoW Coin Monitor | finished {report.get('finished_at', '')} UTC")
    print(f"Sources OK: {', '.join(report.get('sources_ok', []))}")
    if report.get("sources_failed"):
        print(f"Sources FAILED: {', '.join(report['sources_failed'])}")
    print(f"Qualified leads: {report.get('total_leads', 0)} | New: {report.get('new_count', 0)}")
    if report.get("dry_run"):
        print("(dry-run: no Telegram sent)")
    elif report.get("telegram_sent"):
        print("Telegram: sent")
    else:
        print("Telegram: skipped (disabled, no new high-score coins, or not configured)")

    print("-" * 72)
    for i, lead in enumerate(report.get("top_leads", [])[:15], 1):
        print(f"{i:2}. [{lead.get('score', 0):3}] {lead.get('source', '')[:14]:14} | {lead.get('title', '')[:55]}")
        print(f"    {lead.get('url', '')}")
    print("=" * 72)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan internet for new GPU/PoW mineable coins")
    parser.add_argument("--dry-run", action="store_true", help="Scan only, do not send Telegram")
    parser.add_argument("--no-telegram", action="store_true", help="Disable Telegram even if configured")
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    parser.add_argument("--inventory", action="store_true", help="Generate source inventory only")
    parser.add_argument("--config", type=Path, default=None, help="Path to config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    setup_logging(cfg.logging.get("level", "INFO"))

    if args.inventory:
        path = write_inventory(cfg)
        inv = build_inventory(cfg)
        print(json.dumps(inv, ensure_ascii=False, indent=2))
        print(f"\nInventory written to {path}")
        return 0

    report = run_scan(
        cfg,
        dry_run=args.dry_run,
        send_telegram=not args.no_telegram,
    )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_report(report)

    out = PROJECT_ROOT / "data" / "latest_scan.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return 0 if not report.get("sources_failed") or report.get("total_leads", 0) > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
