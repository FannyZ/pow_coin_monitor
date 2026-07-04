#!/usr/bin/env bash
# Sync Cursor/cloud secrets into .env when present (same pattern as btc_trend_monitor)
set -euo pipefail
cd "$(dirname "$0")/.."

write_if_set() {
  local key="$1"
  local val="${!key:-}"
  if [[ -n "$val" ]]; then
    if grep -q "^${key}=" .env 2>/dev/null; then
      sed -i.bak "s|^${key}=.*|${key}=${val}|" .env && rm -f .env.bak
    else
      echo "${key}=${val}" >> .env
    fi
  fi
}

if [[ ! -f .env ]]; then
  cp -n .env.example .env || true
fi

# Reuse Telegram credentials from btc_trend_monitor when available
BTC_ENV="${HOME}/Downloads/btc/btc_trend_monitor/.env"
if [[ -f "$BTC_ENV" ]]; then
  while IFS= read -r line; do
    [[ "$line" =~ ^TELEGRAM_ ]] || continue
    key="${line%%=*}"
    val="${line#*=}"
    if [[ -n "$val" && "$val" != *"你的"* && "$val" != *"123456789"* ]]; then
      export "$key=$val"
    fi
  done < "$BTC_ENV"
fi

if [[ -n "${TELEGRAM_BOT_TOKEN:-}" || -n "${TELEGRAM_CHAT_ID:-}" ]]; then
  write_if_set TELEGRAM_BOT_TOKEN
  write_if_set TELEGRAM_CHAT_ID
fi
