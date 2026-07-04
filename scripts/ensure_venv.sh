#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

venv_ready() {
  [[ -x .venv/bin/python && -x .venv/bin/pip && -f .venv/bin/activate ]]
}

if ! venv_ready; then
  python3 -m venv .venv
fi

if ! venv_ready; then
  echo "ERROR: failed to create .venv" >&2
  exit 1
fi
