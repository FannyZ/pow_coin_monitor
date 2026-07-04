from __future__ import annotations

import logging
import os
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)


class FetchError(Exception):
    pass


def _session() -> requests.Session:
    session = requests.Session()
    proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy") or os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    if proxy:
        session.proxies.update({"http": proxy, "https": proxy})
    return session


def http_get(url: str, cfg: dict[str, Any], accept: str | None = None, referer: str | None = None) -> str:
    headers = {
        "User-Agent": cfg.get("user_agent", "PowCoinMonitor/1.0"),
        "Accept": accept or "text/html,application/xhtml+xml,application/json,*/*",
    }
    if referer:
        headers["Referer"] = referer

    timeout = cfg.get("request_timeout_sec", 25)
    retries = int(cfg.get("request_retries", 2))
    session = _session()
    last_exc: Exception | None = None

    for attempt in range(retries + 1):
        try:
            resp = session.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.text
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            break

    raise FetchError(f"GET {url} failed: {last_exc}") from last_exc


def http_get_json(url: str, cfg: dict[str, Any], referer: str | None = None) -> Any:
    text = http_get(url, cfg, accept="application/json,*/*", referer=referer)
    try:
        import json

        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise FetchError(f"Invalid JSON from {url}") from exc
