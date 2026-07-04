#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

SECRETS="$ROOT/.cursor/mcp.secrets.env"
FITNESS_SECRETS="$HOME/Downloads/fitness/.cursor/mcp.secrets.env"

if [[ ! -f "$SECRETS" && -f "$FITNESS_SECRETS" ]]; then
  cp "$FITNESS_SECRETS" "$SECRETS"
  echo "Copied GitHub MCP secrets from fitness project."
fi

if [[ -f "$SECRETS" ]]; then
  # shellcheck disable=SC1090
  source "$SECRETS"
fi

bash "$ROOT/.cursor/scripts/cloud-agent-install.sh"

# Sync Telegram from btc_trend_monitor if present
BTC_ENV="$HOME/Downloads/btc/btc_trend_monitor/.env"
if [[ -f "$BTC_ENV" ]]; then
  bash "$ROOT/scripts/bootstrap_env.sh"
fi

echo "Setup done. Launch Cursor from terminal after: source .cursor/mcp.secrets.env"
