#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

chmod +x scripts/ensure_venv.sh scripts/bootstrap_env.sh 2>/dev/null || true
./scripts/ensure_venv.sh

# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

./scripts/bootstrap_env.sh

if [[ ! -f .env ]]; then
  echo "请先复制 .env.example 为 .env，并填写 TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID"
  cp -n .env.example .env || true
fi

python3 main.py "$@"
