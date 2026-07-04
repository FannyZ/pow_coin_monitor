#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
chmod +x run.sh scripts/*.sh 2>/dev/null || true
echo "pow_coin_monitor cloud agent install complete."
