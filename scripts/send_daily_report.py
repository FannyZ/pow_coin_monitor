#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pow_monitor.notify.formatting import format_daily_report


def _parse_sources(items: list[str]) -> list[dict[str, str] | str]:
    parsed: list[dict[str, str] | str] = []
    for item in items:
        if "|" in item:
            name, url = item.split("|", 1)
            parsed.append({"name": name.strip(), "url": url.strip()})
        else:
            parsed.append(item.strip())
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Send daily Telegram report from latest_scan.json")
    parser.add_argument("--scan-file", type=Path, default=ROOT / "data" / "latest_scan.json")
    parser.add_argument("--searches", type=int, default=0, help="Number of web searches performed")
    parser.add_argument(
        "--source-added",
        action="append",
        default=[],
        help="Added source as 'name|url' (repeatable)",
    )
    parser.add_argument("--discovered-written", type=int, default=0)
    parser.add_argument("--pushed", action="store_true")
    parser.add_argument("--pending-url", action="append", default=[], help="Pending URLs from inventory")
    parser.add_argument("--dry-run", action="store_true", help="Print message only")
    args = parser.parse_args()

    if not args.scan_file.exists():
        print(f"Scan file not found: {args.scan_file}", file=sys.stderr)
        return 1

    scan = json.loads(args.scan_file.read_text(encoding="utf-8"))
    learning = {
        "searches": args.searches,
        "sources_added": _parse_sources(args.source_added),
        "discovered_written": args.discovered_written,
        "pushed": args.pushed,
        "pending_urls": args.pending_url,
    }
    text = format_daily_report(scan, learning)

    if args.dry_run:
        print(text)
        return 0

    from pow_monitor.config import load_config
    from pow_monitor.notify.telegram import send_telegram_message

    cfg = load_config()
    ok = send_telegram_message(cfg.telegram_bot_token, cfg.telegram_chat_id, text)
    if not ok:
        print("Telegram send failed", file=sys.stderr)
        return 1
    print("Telegram daily report sent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
